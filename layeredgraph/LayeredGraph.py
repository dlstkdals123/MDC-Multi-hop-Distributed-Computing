from typing import Dict, List, Tuple

from layeredgraph import LayerNode, LayerNodePair
from config import NetworkConfig, ModelConfig
from job import JobInfo
from job.DNNModels import DNNModels
from scheduling import *

import importlib
import time
import numpy as np
import copy
import pandas as pd
import glob
import torch

class LayeredGraph:
    def __init__(self, network_config: NetworkConfig, model_config: ModelConfig):
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self._network_config = network_config
        self._dnn_models = DNNModels(model_config, self._device)
        
        self._layered_graph = dict()
        self._layered_graph_backlog: Dict[LayerNodePair, float] = dict()

        self._scheduling_algorithm = None

        self.init_graph()
        self.init_algorithm()
        

    def set_backlogs(self, links: Dict[LayerNodePair, float]) -> None:
        for link, backlog in links.items():
            self._layered_graph_backlog[link] = backlog

    def init_graph(self):
        for source_ip in self._network_config.get_network_list():
            source = LayerNode(source_ip, self._network_config.get_models(source_ip))
            self._layered_graph.setdefault(source, [])

            for destination_ip in self._network_config.get_network_neighbors(source_ip):
                destination = LayerNode(destination_ip, self._network_config.get_models(destination_ip))
                self._layered_graph[source].append(destination)
                link = LayerNodePair(source, destination)
                self._layered_graph_backlog.setdefault(link, 0)

        for source_ip in self._network_config.get_network_list():
            if source_ip in self._network_config.router:
                continue
            
            source = LayerNode(source_ip, self._network_config.get_models(source_ip))
            self._layered_graph.setdefault(source, [])
            self._layered_graph[source].append(source)
            self._layered_graph_backlog.setdefault(LayerNodePair(source, source), 0)

    def init_algorithm(self):
        module_path = self._network_config.scheduling_algorithm.replace(".py", "").replace("/", ".")
        self._algorithm_class = module_path.split(".")[-1]
        self._scheduling_algorithm = getattr(importlib.import_module(module_path), self._algorithm_class)()
        
    def schedule(self, job_info: JobInfo) -> List[Tuple[LayerNode, LayerNode, str]]:
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