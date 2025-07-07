from typing import Dict, List, Tuple

from layeredgraph import LayerNode, LayerNodePair
from config import NetworkConfig, ModelConfig
from job import JobInfo
from scheduling import *

import importlib
import time
import numpy as np
import copy
import pandas as pd
import glob

class LayeredGraph:
    def __init__(self, network_config: NetworkConfig, model_config: ModelConfig):
        self._network_config = network_config
        self._network = network_config.get_network()
        self._model_config = model_config
        self._layered_graph = dict()
        self._layered_graph_backlog = dict()
        self._layer_nodes = []
        self._layer_node_pairs: List[LayerNodePair] = []
        self._scheduling_algorithm = None
        self._previous_update_time = time.time()
        self._capacity = dict()

        self._max_layer_depth = 0
        
        self._alpha = 0.5
        self._expected_arrival_rate = 0

        self._network_performance_info = None
        self._idle_network_performance_info = None

        self._configs = None
        self.init_graph()
        self.init_algorithm()
        self.init_network_performance_info()
        

    def set_graph(self, links: Dict[LayerNodePair, float]) -> None:
        self._previous_update_time = time.time()
        for link, backlog in links.items():
            self.set_link(link, backlog)

    def set_capacity(self, source_ip: str, computing_capacity: float, transfer_capacity: float) -> None:
        for destination_ip in self._capacity[source_ip]:
            capacity = computing_capacity if source_ip == destination_ip else transfer_capacity
            self._capacity[source_ip][destination_ip] = capacity
    
    def update_path_backlog(self, job_info: JobInfo, path: List[Tuple[LayerNode, LayerNode, str]]) -> None:
        input_size = job_info.get_input_size()
        last_transfer_ratio = 1.0;
        for source_node, destination_node, model_name in path:
            link = LayerNodePair(source_node, destination_node)
            if source_node.is_same_node(destination_node):
                ratio = self._model_config.get_computing_ratio(model_name)
                last_transfer_ratio = self._model_config.get_transfer_ratio(model_name)
            else:
                ratio = last_transfer_ratio
            
            self._layered_graph_backlog[link] += ratio * input_size
        
    def update_graph(self):
        current_time = time.time()
        elapsed_time = current_time - self._previous_update_time
        
        links_job_num = self._count_active_jobs()
        self._update_backlog(elapsed_time, links_job_num)
        self._previous_update_time = time.time()

    def _count_active_jobs(self) -> Dict[str, Dict[str, int]]:
        links_job_num = {}

        for link in self._layer_node_pairs:
            source_ip = link.get_source().get_ip()
            dest_ip = link.get_destination().get_ip()
            
            if source_ip not in links_job_num:
                links_job_num[source_ip] = {}
            if dest_ip not in links_job_num[source_ip]:
                links_job_num[source_ip][dest_ip] = 0
                
            if self._layered_graph_backlog[link] > 0:
                links_job_num[source_ip][dest_ip] += 1
        
        return links_job_num

    def _update_backlog(self, elapsed_time: float, links_job_num: Dict[str, Dict[str, int]]):
        for link in self._layer_node_pairs:
            source_ip = link.get_source().get_ip()
            dest_ip = link.get_destination().get_ip()
            
            job_count = links_job_num[source_ip][dest_ip]
            capacity = self._capacity[source_ip][dest_ip]

            if job_count > 0:
                computing_delta = elapsed_time * capacity / job_count
                self._layered_graph_backlog[link] = max(0, self._layered_graph_backlog[link] - computing_delta)

    def set_link(self, link: LayerNodePair, backlog: float):
        self._layered_graph_backlog[link] = backlog

    def init_graph(self):
        for source_ip in self._network:
            source = LayerNode(source_ip, self._network_config.get_models()[source_ip])
            self._layer_nodes.append(source)
            self._layered_graph.setdefault(source, [])
            self._capacity.setdefault(source_ip, {})

            for destination_ip in self._network[source_ip]:
                self._capacity[source_ip].setdefault(destination_ip, 0)
                destination = LayerNode(destination_ip, self._network_config.get_models()[destination_ip])
                self._layered_graph[source].append(destination)
                link = LayerNodePair(source, destination)
                self._layer_node_pairs.append(link)
                self._layered_graph_backlog.setdefault(link, 0)

        for source_ip in self._network:
            if source_ip in self._network_config.get_router():
                continue
            
            source = LayerNode(source_ip, self._network_config.get_models()[source_ip])
            self._capacity[source_ip].setdefault(source_ip, 0)
            self._layered_graph.setdefault(source, [])
            self._layered_graph[source].append(source)
            self._layer_node_pairs.append(LayerNodePair(source, source))
            self._layered_graph_backlog.setdefault(LayerNodePair(source, source), 0)

    def init_algorithm(self):
        module_path = self._network_config.get_scheduling_algorithm().replace(".py", "").replace("/", ".")
        self._algorithm_class = module_path.split(".")[-1]
        self._scheduling_algorithm = getattr(importlib.import_module(module_path), self._algorithm_class)()
        
    def schedule(self, source_ip: str, job_info: JobInfo) -> List[Tuple[LayerNode, LayerNode, str]]:
        source_node = LayerNode(source_ip, self._network_config.get_models()[source_ip])
        destination_node = LayerNode(job_info.get_terminal_destination(), self._network_config.get_models()[job_info.get_terminal_destination()])

        input_size = job_info.get_input_size()
    
        # if self._algorithm_class == 'JDPCRA':
        #     path = self._scheduling_algorithm.get_path(source_node, destination_node, self._layered_graph, self._model_configs, self._expected_arrival_rate, self._network_performance_info, input_size)
        
        # elif self._algorithm_class == 'TLDOC':
        #     if self._configs == None:
        #         idle_power = self.load_config()
        #         self._scheduling_algorithm.init_parameter(self._configs[0], self._configs[1], idle_power, self._model_configs)
        #     self._scheduling_algorithm.set_t_wait(self.get_t_wait())
        #     path = self._scheduling_algorithm.get_path(source_node, destination_node, self._layered_graph, self._expected_arrival_rate, self._network_performance_info, input_size)
        
        if self._algorithm_class == 'RandomSelection':
            self._scheduling_algorithm: RandomSelection
            path = self._scheduling_algorithm.get_path(source_node, destination_node, self._layered_graph)
        
        else:
            raise ValueError(f"Invalid scheduling algorithm: {self._algorithm_class}")
        
        return path
    
    # Method that return all layered grph's links of layer_node_ip.
    # ex) layer_node_ip : 192.168.1.5
    # return : LayerNodePair(192.168.1.5-0, 192.168.1.6-0), LayerNodePair(192.168.1.5-1, 192.168.1.6-1) ...
    def get_links(self, layer_node_ip: str):
        links = []
        layer_node = LayerNode(layer_node_ip, self._network_config.get_models()[layer_node_ip])

        neighbors = self._layered_graph[layer_node]
        for neighbor in neighbors:
            link = LayerNodePair(layer_node, neighbor)

            links.append(link)

        return links
    
    def get_layered_graph_backlog(self):
        return self._layered_graph_backlog
    
    def get_arrival_rate(self, path: List[Tuple[LayerNode, LayerNode, str]]) -> float:
        arrival_rate = 0
        for source, destination, _ in path:
            link = LayerNodePair(source, destination)
            arrival_rate += self._layered_graph_backlog[link]

        return arrival_rate

    def update_expected_arrival_rate(self, slot_arrival_rate):
        """TODO: 이번 time slot에 들어온 job rate(slot_arrival_rate)(i.e., 강화학습이 처리한 프레임의 개수)를 기반으로 arrival rate를 계산한다.
        """
        self._expected_arrival_rate = self._alpha * self._expected_arrival_rate + (1-self._alpha) * slot_arrival_rate
        

    def init_network_performance_info(self):
        """TODO: 각 (end), edge, cloud에 대해서 total computing resource를 self._network_performance_info에 저장한다.
        * format: computing_capacities = {'end':, 'edge':, 'cloud'}, transmission_rates = {'end':, 'edge':}
        """
        computing_capacities = {
            'end' : 235.8,
            'edge' : 1280.0,
            'cloud' : 9098.0
        }
        transmission_rates = {
            'end' : 1000,
            'edge' : 1000
        }
        
        self._idle_network_performance_info = (computing_capacities, transmission_rates)
        self._network_performance_info = copy.deepcopy(self._idle_network_performance_info)
        
        
    def update_network_performance_info(self, node_name, ratio):
        """TODO: 현재 time slot에서 각 (end), edge, cloud에 대해서 idle computing resource를 self._network_performance_info에 저장한다."""
        self._network_performance_info[0][node_name] = self._idle_network_performance_info[0][node_name] * ratio
    
    
    def load_config(self, config_path=None):
        """TODO: path에 있는 파일에서 저장된 config value를 (layer별 time, energy) 불러와서 self._configs에 저장하고 power는 반환한다."""

        end_config_path = glob.glob("spec/yolov5/end.csv")[0]
        edge_config_path = glob.glob("spec/yolov5/edge.csv")[0]
        cloud_config_path = glob.glob("spec/yolov5/cloud.csv")[0]
        end_to_edge_config_path = glob.glob("spec/yolov5/end_to_edge.csv")[0]

        end_config = pd.read_csv(end_config_path)
        edge_config = pd.read_csv(edge_config_path)
        cloud_config = pd.read_csv(cloud_config_path)
        end_to_edge_config = pd.read_csv(end_to_edge_config_path)

        time_config = {
            'end': end_config.latency.to_list(),
            'edge': edge_config.latency.to_list(),
            'cloud': cloud_config.latency.to_list()
        }

        energy_config = {
            'end': end_config.watt_hour.to_list(),
            'edge': edge_config.watt_hour.to_list(),
            'cloud': cloud_config.watt_hour.to_list(),
            'end_to_edge': end_to_edge_config.watt_hour.to_list(),
        }

        self._configs = (time_config, energy_config)

        return 1.7 # 측정 결과 초당 1.7w를 소모함
    
    def get_t_wait(self):
        computing_backlog = {
            "end": 0,
            "edge": 0,
            "cloud": 0
        }
        transfer_backlog = {
            "end": 0,
            "edge": 0,
            "cloud": 0
        }

        for link in self._layer_node_pairs:
            if link.get_source().get_ip() == "192.168.1.5":
                node_name = "end"   
            elif link.get_source().get_ip() == "192.168.1.7":
                node_name = "edge"
            elif link.get_source().get_ip() == "192.168.1.8":
                node_name = "cloud"

            if link.is_same_node(): # computing
                computing_backlog[node_name] += self._layered_graph_backlog[link]
            else: # transfer
                transfer_backlog[node_name] += self._layered_graph_backlog[link]


        end_wait_time = computing_backlog["end"] / self._network_performance_info[0]["end"] + transfer_backlog["end"] / self._network_performance_info[1]["end"]
        edge_wait_time = computing_backlog["edge"] / self._network_performance_info[0]["edge"] + transfer_backlog["edge"] / self._network_performance_info[1]["edge"]
        cloud_wait_time = computing_backlog["cloud"] / self._network_performance_info[0]["cloud"]

        return end_wait_time + edge_wait_time + cloud_wait_time