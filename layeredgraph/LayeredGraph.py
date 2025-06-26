from typing import Dict, List

from config import NetworkConfig, ModelConfig
from layeredgraph import LayerNode, LayerNodePair
from job import JobInfo
from job.DNNModels import DNNModels
from scheduling import Dijkstra, JDPCRA, TLDOC

import importlib
import time
import numpy as np
import copy
import pandas as pd
import glob

class LayeredGraph:
    def __init__(self, network_config: NetworkConfig, model_configs: Dict[str, ModelConfig] = None):
        self._network_config = network_config
        self._network = network_config.get_network()
        self._layered_graph = dict()
        self._layered_graph_backlog = dict()
        self._layer_nodes = []
        self._layer_node_pairs: List[LayerNodePair] = []
        self._scheduling_algorithm = None
        self._previous_update_time = time.time()
        self._capacity = dict()

        # layer 개념 제거 - 모든 노드는 layer 0으로 통일
        self._max_layer_depth = 1

        self._dnn_models = DNNModels(self._network_config, "cpu", "192.168.1.2", model_configs)
        
        self._alpha = 0.5
        self._expected_arrival_rate = 0

        self._network_performance_info = None
        self._idle_network_performance_info = None

        self._configs = None
        self.init_graph()
        self.init_algorithm()
        self.init_network_performance_info()
        

    def set_graph(self, links):
        self._previous_update_time = time.time()
        for link in links:
            link: LayerNodePair
            self.set_link(link, links[link])

    def set_capacity(self, source_ip: str, computing_capacity: float, transfer_capacity: float):
        for destination_ip in self._capacity[source_ip]:
            if source_ip == destination_ip:
                self._capacity[source_ip][destination_ip] = computing_capacity
            else:
                self._capacity[source_ip][destination_ip] = transfer_capacity
    
    def update_path_backlog(self, job_info: JobInfo, path: List[LayerNode]):
        input_size = job_info.get_input_size()
        job_name = job_info.get_job_name()
        
        # 단순화: 모든 노드가 전체 모델을 처리하므로 layer 구분 없음
        for i in range(len(path) - 1):
            source_layer_node: LayerNode = path[i]
            destination_layer_node: LayerNode = path[i + 1]
            link = LayerNodePair(source_layer_node, destination_layer_node)

            if source_layer_node.is_same_node(destination_layer_node):
                # 같은 노드 내에서의 처리 (계산)
                self._layered_graph_backlog[link] += self._dnn_models.get_computing(job_name, 0) * input_size
            else:
                # 다른 노드로의 전송
                self._layered_graph_backlog[link] += self._dnn_models.get_transfer(job_name, 0) * input_size
        
    def update_graph(self):
        current_time = time.time()
        elapsed_time = current_time - self._previous_update_time

        links_job_num = {}

        for link in self._layer_node_pairs:
            link: LayerNodePair
            source_node_ip = link.get_source().get_ip()
            destination_node_ip = link.get_destination().get_ip()

            destinations: Dict = links_job_num.setdefault(source_node_ip, {})
            destinations.setdefault(destination_node_ip, 0)

            if self._layered_graph_backlog[link] > 0:
                destinations[destination_node_ip] += 1

        for link in self._layer_node_pairs:
            link: LayerNodePair
            source_node_ip = link.get_source().get_ip()
            destination_node_ip = link.get_destination().get_ip()
            
            link_job_num = links_job_num[source_node_ip][destination_node_ip]
            capacity = self._capacity[source_node_ip][destination_node_ip]

            if link_job_num > 0:
                job_computing_delta = elapsed_time * capacity / link_job_num

                self._layered_graph_backlog[link] = max(0, self._layered_graph_backlog[link] - job_computing_delta)

        self._previous_update_time = time.time()

    def set_link(self, link: LayerNodePair, backlog: float):
        self._layered_graph_backlog[link] = backlog

    def init_graph(self):
        # 단순화: 모든 노드는 layer 0으로 통일
        self._max_layer_depth = 1

        for layer in range(self._max_layer_depth):
            for source_ip in self._network:
                source = LayerNode(source_ip, layer)
                self._layer_nodes.append(source)

                if source not in self._layered_graph:
                    self._layered_graph[source] = []

                if source_ip not in self._capacity:
                    self._capacity[source_ip] = dict()

                for destination_ip in self._network[source_ip]:
                    if destination_ip not in self._capacity[source_ip]:
                        self._capacity[source_ip][destination_ip] = 0

                    destination = LayerNode(destination_ip, layer)

                    self._layered_graph[source].append(destination)

                    link = LayerNodePair(source, destination)

                    self._layer_node_pairs.append(link)
                    self._layered_graph_backlog[link] = 0

        # layer 간 연결 제거 (모든 노드가 같은 layer에 있음)

    def init_algorithm(self):
        module_path = self._network_config.get_scheduling_algorithm().replace(".py", "").replace("/", ".")
        self._algorithm_class = module_path.split(".")[-1]
        self._scheduling_algorithm = getattr(importlib.import_module(module_path), self._algorithm_class)()
        
    def schedule(self, source_ip: str, job_info: JobInfo):
        # 단순화: 모든 노드는 layer 0
        source_node = LayerNode(source_ip, 0)
        destination_node = LayerNode(job_info.get_terminal_destination(), 0)

        input_size = job_info.get_input_size()
    
        if self._algorithm_class == 'JDPCRA':
            self._scheduling_algorithm: JDPCRA
            path = self._scheduling_algorithm.get_path(source_node, destination_node, self._layered_graph, self._dnn_models._yolo_computing_ratios, self._dnn_models._yolo_transfer_ratios, self._expected_arrival_rate, self._network_performance_info, input_size)
        
        elif self._algorithm_class == 'TLDOC':
            self._scheduling_algorithm: TLDOC
            if self._configs == None:
                idle_power = self.load_config()
                self._scheduling_algorithm.init_parameter(self._configs[0], self._configs[1], idle_power, self._dnn_models._yolo_transfer_ratios)
                print("init configs")
            self._scheduling_algorithm.set_t_wait(self.get_t_wait())
            path = self._scheduling_algorithm.get_path(source_node, destination_node, self._layered_graph, self._expected_arrival_rate, self._network_performance_info, input_size)
        
        else:
            path = self._scheduling_algorithm.get_path(source_node, destination_node, self._layered_graph, self._layered_graph_backlog, self._layer_nodes)
        
        return path
    
    def get_links(self, layer_node_ip: str):
        links = []
        for layer in range(self._max_layer_depth):
            layer_node = LayerNode(layer_node_ip, layer)

            neighbors = self._layered_graph[layer_node]
            for neighbor in neighbors:
                link = LayerNodePair(layer_node, neighbor)

                links.append(link)

        return links
    
    def get_layered_graph_backlog(self):
        return self._layered_graph_backlog
    
    def get_arrival_rate(self,path):
        arrival_rate = 0
        for i in range(len(path) - 1):
            source = path[i]
            destination = path[i + 1]

            link = LayerNodePair(source = source, destination = destination)
            
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

            # transfer
            if link.is_same_layer():
                transfer_backlog[node_name] += self._layered_graph_backlog[link]
            
            # compute
            elif link.is_same_node():
                computing_backlog[node_name] += self._layered_graph_backlog[link]


        end_wait_time = computing_backlog["end"] / self._network_performance_info[0]["end"] + transfer_backlog["end"] / self._network_performance_info[1]["end"]
        edge_wait_time = computing_backlog["edge"] / self._network_performance_info[0]["edge"] + transfer_backlog["edge"] / self._network_performance_info[1]["edge"]
        cloud_wait_time = computing_backlog["cloud"] / self._network_performance_info[0]["cloud"]

        return end_wait_time + edge_wait_time + cloud_wait_time