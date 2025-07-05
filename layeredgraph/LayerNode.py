from typing import List
class LayerNode:
    """
    LayeredGraph의 노드를 나타내는 클래스입니다.
    """
    
    def __init__(self, ip: str, model_names: list[str] = []):
        """
        LayerNode 객체를 초기화합니다.
        
        Args:
            ip (str): 노드의 IP 주소
            model_names (list[str]): 노드에서 실행 가능한 모델 이름 목록
        """
        self._ip = ip
        self._model_names = model_names

    @property
    def ip(self) -> str:
        return self._ip
    
    @property
    def model_names(self) -> list[str]:
        return self._model_names

    def is_same_node(self, other: 'LayerNode') -> bool:
        return self._ip == other.ip

    def to_string(self) -> str:
        return self._ip

    def __hash__(self) -> int:
        return hash(self._ip)

    def __str__(self) -> str:
        return self._ip

    def __repr__(self) -> str:
        return self._ip

    def __eq__(self, other: 'LayerNode') -> bool:
        if not isinstance(other, LayerNode):
            return False
        return self._ip == other._ip

    def __ne__(self, other):
        return not(self == other)
    
    def __lt__(self, other):
        return self.get_ip() < other.get_ip()
    