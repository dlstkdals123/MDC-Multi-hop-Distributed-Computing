from typing import Dict
from layeredgraph import LayerNodePair
from communication.Performance import Performance

class NodeLinkInfo:
    """
    노드의 링크 정보를 저장하는 클래스입니다.

    Attributes:
        _ip (str): 노드의 IP 주소.
        _links (Dict[LayerNodePair, float]): 노드의 링크 정보와 총 계산량 또는 전송량 (KB or GFLOPs).
        _performance (Performance): 노드의 성능 정보.
    """
    def __init__(self, ip: str, links: Dict[LayerNodePair, float], performance: Performance):
        self._check_validate(ip)

        self._ip: str = ip
        self._links: Dict[LayerNodePair, float] = links

        self._performance: Performance = performance

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
    def performance(self) -> Performance:
        return self._performance