from layeredgraph import LayerNode, LayerNodePair
import random

class RandomSelection:
    def __init__(self):
        pass

    def get_path(self, source_node: LayerNode, destination_node: LayerNode, layered_graph, layered_graph_backlog, layer_nodes, model_name: str):
        possible_paths = []
        for node in layer_nodes:
            if node.get_ip() == source_node.get_ip():
                for neighbor in layered_graph[node]:
                    if neighbor.get_ip() == destination_node.get_ip():
                        possible_paths.append([node, neighbor])
        
        return random.choice(possible_paths)