from typing import Dict, List, Tuple
import importlib
import time
import torch

from config import NetworkConfig, ModelConfig
from layeredgraph import LayerNode, LayerNodePair
from job import JobInfo
from job.DNNModels import DNNModels
from scheduling import RandomSelection

MS_PER_SECOND = 1000

class LayeredGraph:
    """
    레이어드 그래프를 관리하는 클래스입니다.
    네트워크 토폴로지, 노드, 링크, 스케줄링 알고리즘 등을 초기화하고 관리합니다.
    각 링크의 백로그 및 용량(capacity) 정보를 저장하며, 스케줄링 알고리즘을 통해 경로를 계산합니다.

    Attributes:
        _network_config (NetworkConfig): 네트워크 설정 정보.
        _dnn_models (DNNModels): 모델 모음.
        _layered_graph (Dict[LayerNode, List[LayerNode]]): 노드와 노드의 이웃 노드들을 저장하는 레이어드 그래프.
        _layered_graph_backlog (Dict[LayerNodePair, float]): 노드들의 쌍으로 이루어진 링크와 해당 링크의 백로그를 저장하는 레이어드 그래프.
        _scheduling_algorithm: 스케줄링 알고리즘.
        _previous_update_time (float): 마지막 업데이트 시간.
        _capacity (Dict[str, Dict[str, float]]): 레이어드 그래프의 .
    """

    def __init__(self, network_config: NetworkConfig, model_config: ModelConfig):
        """
        Args:
            network_config (NetworkConfig): 네트워크 설정 정보.
            model_config (ModelConfig): 모델 설정 정보.
        """
        self._network_config = network_config

        self._dnn_models = DNNModels(model_config, "cuda" if torch.cuda.is_available() else "cpu")

        self._layered_graph: Dict[LayerNode, List[LayerNode]] = dict()
        self._layered_graph_backlog: Dict[LayerNodePair, float] = dict()

        self._scheduling_algorithm = None
        self._previous_update_time: float = time.time() * MS_PER_SECOND
        self._capacity: Dict[str, Dict[str, float]] = dict()

        self.init_graph()
        self.init_algorithm()
        
    def set_graph(self, links: Dict[LayerNodePair, float]) -> None:
        """
        링크별 백로그 정보를 받아 그래프를 갱신합니다.

        Args:
            links (Dict[LayerNodePair, float]): 각 링크와 해당 백로그 값의 딕셔너리.
        """
        self._previous_update_time = time.time() * MS_PER_SECOND
        for link, backlog in links.items():
            self.set_link(link, backlog)

    def set_capacity(self, source_ip: str, computing_capacity: float, transfer_capacity: float) -> None:
        """
        소스 IP 기준으로 각 목적지 IP에 대한 용량(capacity)을 설정합니다.

        Args:
            source_ip (str): 소스 노드의 IP.
            computing_capacity (float): 계산 용량(GFLOPs).
            transfer_capacity (float): 전송 용량(KB).
        """
        for destination_ip in self._capacity[source_ip]:
            capacity = computing_capacity if source_ip == destination_ip else transfer_capacity
            self._capacity[source_ip][destination_ip] = capacity
    
    def update_path_backlog(self, job_info: JobInfo, path: List[Tuple[LayerNode, LayerNode, str]]) -> None:
        """
        경로 상의 각 링크에 대해 백로그를 업데이트합니다.

        Args:
            job_info (JobInfo): 작업 정보.
            path (List[Tuple[LayerNode, LayerNode, str]]): (소스, 목적지, 모델명) 튜플의 리스트.
        """
        for source_node, destination_node, model_name in path:
            link = LayerNodePair(source_node, destination_node)
            if source_node.is_same_node(destination_node):
                capacity = self._dnn_models.get_computing(model_name)
            else:
                if model_name == "":
                    capacity = job_info.input_bytes
                else:
                    capacity = self._dnn_models.get_transfer(model_name)
            
            # GFLOPs 또는 KB 단위로 백로그 증가
            self._layered_graph_backlog[link] += capacity
        
    def update_graph(self):
        """
        경과 시간에 따라 각 링크의 백로그를 감소시킵니다.
        """
        current_time = time.time() * MS_PER_SECOND
        elapsed_time = current_time - self._previous_update_time
        
        links_job_num = self._count_active_jobs()
        self._update_backlog(elapsed_time, links_job_num)
        self._previous_update_time = current_time

    def _count_active_jobs(self) -> Dict[str, Dict[str, int]]:
        """
        각 링크별 활성화된 작업(백로그가 0보다 큰 경우) 개수를 계산합니다.

        Returns:
            Dict[str, Dict[str, int]]: 소스 IP별 목적지 IP별 활성 작업 수.
        """
        links_job_num = {}

        for link in self._layered_graph_backlog.keys():
            source_ip = link.source.get_ip()
            dest_ip = link.destination.get_ip()
            
            if source_ip not in links_job_num:
                links_job_num[source_ip] = {}
            if dest_ip not in links_job_num[source_ip]:
                links_job_num[source_ip][dest_ip] = 0
                
            if self._layered_graph_backlog[link] > 0:
                links_job_num[source_ip][dest_ip] += 1
        
        return links_job_num

    def _update_backlog(self, elapsed_time: float, links_job_num: Dict[str, Dict[str, int]]):
        """
        경과 시간과 활성 작업 수에 따라 각 링크의 백로그를 감소시킵니다.

        Args:
            elapsed_time (float): 이전 업데이트 이후 경과 시간(초).
            links_job_num (Dict[str, Dict[str, int]]): 각 링크별 활성 작업 수.
        """
        for link in self._layered_graph_backlog.keys():
            source_ip = link.source.get_ip()
            dest_ip = link.destination.get_ip()
            
            job_count = links_job_num[source_ip][dest_ip]
            capacity = self._capacity[source_ip][dest_ip]

            if job_count > 0:
                # 각 작업에 할당된 용량만큼 백로그 감소
                computing_delta = elapsed_time * capacity / job_count
                self._layered_graph_backlog[link] = max(0, self._layered_graph_backlog[link] - computing_delta)

    def set_link(self, link: LayerNodePair, backlog: float):
        self._layered_graph_backlog[link] = backlog

    def init_graph(self):
        """
        네트워크 설정을 기반으로 레이어드 그래프와 노드, 링크, 용량 정보를 초기화합니다.
        """
        for source_ip in self._network_config.get_network_list():
            source = LayerNode(source_ip, self._network_config.get_models(source_ip))
            self._layered_graph.setdefault(source, [])
            self._capacity.setdefault(source_ip, {})

            for destination_ip in self._network_config.get_network_neighbors(source_ip):
                self._capacity[source_ip].setdefault(destination_ip, 0)
                destination = LayerNode(destination_ip, self._network_config.get_models(destination_ip))
                self._layered_graph[source].append(destination)
                link = LayerNodePair(source, destination)
                self._layered_graph_backlog.setdefault(link, 0)

        for source_ip in self._network_config.get_network_list():
            if source_ip in self._network_config.router:
                continue
            
            source = LayerNode(source_ip, self._network_config.get_models(source_ip))
            self._capacity[source_ip].setdefault(source_ip, 0)
            self._layered_graph.setdefault(source, [])
            self._layered_graph[source].append(source)
            self._layered_graph_backlog.setdefault(LayerNodePair(source, source), 0)

    def init_algorithm(self):
        """
        네트워크 설정에 명시된 스케줄링 알고리즘을 동적으로 import하여 초기화합니다.
        """
        module_path = self._network_config.scheduling_algorithm.replace(".py", "").replace("/", ".")
        self._algorithm_class = module_path.split(".")[-1]
        self._scheduling_algorithm = getattr(importlib.import_module(module_path), self._algorithm_class)()
        
    def schedule(self, job_info: JobInfo) -> List[Tuple[LayerNode, LayerNode, str]]:
        """
        스케줄링 알고리즘을 이용해 작업의 경로를 계산합니다.

        Args:
            job_info (JobInfo): 작업 정보.

        Returns:
            List[Tuple[LayerNode, LayerNode, str]]: (소스, 목적지, 모델명) 튜플의 리스트.
        """
        source_node = LayerNode(job_info.source_ip, self._network_config.get_models(job_info.source_ip))
        destination_node = LayerNode(job_info.terminal_ip, self._network_config.get_models(job_info.terminal_ip))
        
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
        layer_node = LayerNode(layer_node_ip, self._network_config.get_models(layer_node_ip))

        neighbors = self._layered_graph[layer_node]
        for neighbor in neighbors:
            link = LayerNodePair(layer_node, neighbor)

            links.append(link)

        return links
    
    def get_layered_graph_backlog(self) -> Dict[LayerNodePair, float]:
        """
        레이어드 그래프의 각 링크의 백로그를 반환합니다. (GFLOPs or KB)
        """
        return self._layered_graph_backlog