from layeredgraph import LayerNode, LayerNodePair
import random
from typing import Dict, List
from config.ModelConfig import ModelConfig

class RandomSelection:
    def __init__(self):
        pass

    def get_path(self, source_node: LayerNode, destination_node: LayerNode, layered_graph: Dict[LayerNode, List[LayerNode]]):
        """
        랜덤 선택 알고리즘을 구현한 클래스입니다.

        Args:
            source_node (LayerNode): 출발 노드
            destination_node (LayerNode): 도착 노드
            layered_graph (Dict[LayerNode, List[LayerNode]]): 레이어드 그래프

        Returns:
            List[LayerNode, LayerNode, str]: 경로
            예시1: [["192.168.1.5", "192.168.1.6", ""], ["192.168.1.6", "192.168.1.6", "yolov5"], ["192.168.1.6", "192.168.1.8", ""]]

            예시2: [["192.168.1.5", "192.168.1.6", ""], ["192.168.1.6", "192.168.1.8", ""], ["192.168.1.8", "192.168.1.8", "yolov5"]]

            예시3: [["192.168.1.5", "192.168.1.6", ""], ["192.168.1.6", "192.168.1.8", ""]]
        """
        possible_paths = []
        visited_models = set()
        prop = 0.5
        current_node = source_node

        while True:
            neighbor_list = layered_graph[current_node].copy()
            if current_node in neighbor_list:
                neighbor_list.remove(current_node)
            
            # 사용하지 않은 모델 리스트
            not_visited_model_names = [model_name for model_name in current_node.get_model_names() if model_name not in visited_models]

            # 사용하지 않은 모델이 없다면 다음 노드로 이동
            # 다음 노드가 없는 마지막 노드라면 종료.
            if len(not_visited_model_names) == 0 and current_node == destination_node:
                break
            
            # 다음 노드로 이동
            if len(not_visited_model_names) == 0:
                random_neighbor = random.choice(neighbor_list)
                possible_paths.append((current_node, random_neighbor, ""))
                current_node = possible_paths[-1][1]
                continue

            # 사용하지 않은 모델 중 하나를 선택하기
            if random.random() < prop:
                random_model_name = random.choice(not_visited_model_names)
                possible_paths.append((current_node, current_node, random_model_name))
                visited_models.add(random_model_name)
                continue

            # 모델을 전부 사용했다면 다음 노드로 이동.
            # 다음 노드가 없는 마지막 노드라면 종료.
            if current_node == destination_node:
                break
            
            # 다음 노드로 이동
            random_neighbor = random.choice(neighbor_list)
            possible_paths.append((current_node, random_neighbor, ""))
            current_node = possible_paths[-1][1]

        return possible_paths