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
        self.check_validate(ip, links, computing_capacity, transfer_capacity)

        self._ip = ip
        self._links = links

        self._computing_capacity = computing_capacity
        self._transfer_capacity = transfer_capacity

    def check_validate(self, ip: str, links: Dict[LayerNodePair, float], computing_capacity: float, transfer_capacity: float):
        """
        IP 주소와 링크 정보가 올바른지 검증합니다.
        """
        if not ip:
            raise ValueError("IP 주소는 빈 문자열이 될 수 없습니다.")
        
        if computing_capacity < 0.0 or computing_capacity > 1.0:
            raise ValueError("계산량은 0.0 ~ 1.0 사이의 실수여야 합니다.")
        
        if transfer_capacity < 0.0 or transfer_capacity > 1.0:
            raise ValueError("전송량은 0.0 ~ 1.0 사이의 실수여야 합니다.")

    def get_ip(self):
        return self._ip

    def get_links(self):
        return self._links
    
    def get_computing_capacity(self):
        return self._computing_capacity
    
    def get_transfer_capacity(self):
        return self._transfer_capacity