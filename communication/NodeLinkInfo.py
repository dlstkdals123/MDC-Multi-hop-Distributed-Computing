from typing import Dict
from layeredgraph import LayerNodePair

class NodeLinkInfo:
    """
    노드의 링크 정보를 저장하는 클래스입니다.

    Attributes:
        _ip (str): 노드의 IP 주소.
        _links (Dict[LayerNodePair, float]): 노드의 링크 정보와 총 계산량.
        _computing_capacity (float): 노드의 평균 계산량.
        _transfer_capacity (float): 노드의 평균 전송량.
    """
    def __init__(self, ip: str, links: Dict[LayerNodePair, float], computing_capacity: float, transfer_capacity: float):
        """
        Args:
            ip (str): 노드의 IP 주소.
            links (Dict[LayerNodePair, float]): 노드의 링크 정보와 총 계산량(전송량).
            computing_capacity (float): 노드의 평균 계산량.
            transfer_capacity (float): 노드의 평균 전송량.
        """
        self._ip = ip
        self._links = links

        self._computing_capacity = computing_capacity
        self._transfer_capacity = transfer_capacity

    def get_ip(self):
        return self._ip

    def get_links(self):
        return self._links
    
    def get_computing_capacity(self):
        return self._computing_capacity
    
    def get_transfer_capacity(self):
        return self._transfer_capacity