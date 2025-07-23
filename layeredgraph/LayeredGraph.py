from typing import Dict, List, Tuple
import importlib
import time
import torch

from config import NetworkConfig, ModelConfig
from layeredgraph import LayerNode, LayerNodePair
from job import JobInfo
from communication.Performance import Performance
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
        self._dnn_models = DNNModels(model_config, self._device)
        
        self._layered_graph = dict()
        self._layered_graph_backlog: Dict[LayerNodePair, float] = dict()
        self._performance: Dict[LayerNode, Performance] = dict()

        self._scheduling_algorithm = None

        self.init_graph()
        self.init_algorithm()
        

    def set_backlogs(self, links: Dict[LayerNodePair, float]) -> None:
        """
        링크별 백로그 정보를 받아 그래프를 갱신합니다.

        Args:
            links (Dict[LayerNodePair, float]): 각 링크와 해당 백로그 값의 딕셔너리.
        """
        for link, backlog in links.items():
            self._layered_graph_backlog[link] = backlog
    
    def set_performance(self, node_ip: str, performance: Performance) -> None:
        node = self._get_layer_node(node_ip)
        self._performance[node] = performance

    def init_graph(self):
        """
        네트워크 설정을 기반으로 레이어드 그래프와 노드, 링크, 용량 정보를 초기화합니다.
        """
        for source_ip in self._network_config.get_network_list():
            source = self._get_layer_node(source_ip)
            self._layered_graph.setdefault(source, [])
            self._performance.setdefault(source, Performance(0, 0, 0, 0, 0))

            for destination_ip in self._network_config.get_network_neighbors(source_ip):
                destination = self._get_layer_node(destination_ip)
                self._layered_graph[source].append(destination)
                link = self._get_layer_node_pair(source_ip, destination_ip)
                self._layered_graph_backlog.setdefault(link, 0)

        # 자기 자신 추가
        for source_ip in self._network_config.get_network_list():
            if source_ip in self._network_config.router:
                continue
            
            source = self._get_layer_node(source_ip)
            self._layered_graph.setdefault(source, [])
            self._layered_graph[source].append(source)
            self._layered_graph_backlog.setdefault(self._get_layer_node_pair(source_ip, source_ip), 0)

    def init_algorithm(self):
        """
        네트워크 설정에 명시된 스케줄링 알고리즘을 동적으로 import하여 초기화합니다.
        """
        module_path = self._network_config.scheduling_algorithm.replace(".py", "").replace("/", ".")
        self._algorithm_class = module_path.split(".")[-1]
        self._scheduling_algorithm = getattr(importlib.import_module(module_path), self._algorithm_class)()

    def _get_layer_node(self, ip: str) -> LayerNode:
        return LayerNode(ip, self._network_config.get_models(ip))

    def _get_layer_node_pair(self, source_ip: str, destination_ip: str) -> LayerNodePair:
        return LayerNodePair(self._get_layer_node(source_ip), self._get_layer_node(destination_ip))
        
    def schedule(self, job_info: JobInfo) -> List[Tuple[LayerNodePair, str]]:
        """
        스케줄링 알고리즘을 이용해 작업의 경로를 계산합니다.

        Args:
            job_info (JobInfo): 작업 정보.

        Returns:
            List[Tuple[LayerNode, LayerNode, str]]: (소스, 목적지, 모델명) 튜플의 리스트.
        """
        source_node = self._get_layer_node(job_info.source_ip)
        destination_node = self._get_layer_node(job_info.terminal_ip)
        
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
        layer_node = self._get_layer_node(layer_node_ip)

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

    def get_performance(self) -> Dict[LayerNode, Performance]:
        """
        레이어드 그래프의 각 노드의 성능을 반환합니다. (KB/ms, GFLOPs/ms)
        """
        return self._performance