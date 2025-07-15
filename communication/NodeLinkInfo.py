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
        self._check_validate(ip)

        self._ip: str = ip
        self._links: Dict[LayerNodePair, float] = links

        self._computing_capacity: float = computing_capacity
        self._transfer_capacity: float = transfer_capacity

    def _check_validate(self, ip: str):
        """
        IP 주소가 올바른지 검증합니다.
        """
        if not ip:
            raise ValueError("IP 주소는 빈 문자열이 될 수 없습니다.")

    @property
    def ip(self) -> str:
        return self._ip
    
    @property
    def links(self) -> Dict[LayerNodePair, float]:
        return self._links
    
    @property
    def computing_capacity(self) -> float:
        return self._computing_capacity
    
    @property
    def transfer_capacity(self) -> float:
        return self._transfer_capacity