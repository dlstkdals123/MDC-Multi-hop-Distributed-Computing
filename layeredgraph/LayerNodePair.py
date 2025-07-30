from layeredgraph import LayerNode

class LayerNodePair:
    """
    노드 쌍을 나타내는 클래스입니다.

    Attributes:
        _source (LayerNode): 소스 노드.
        _destination (LayerNode): 목적지 노드.
    """
    
    def __init__(self, source: LayerNode, destination: LayerNode):
        self._source = source
        self._destination = destination

    @property
    def source(self) -> LayerNode:
        return self._source
    
    @property
    def destination(self) -> LayerNode:
        return self._destination

    def to_string(self) -> str:
        return f"{self._source.to_string()}->{self._destination.to_string()}"
    
    def __hash__(self):
        return hash(self.to_string())
    
    def __str__(self):
        return self.to_string()
    
    def __repr__(self):
        return self.to_string()

    def __eq__(self, other):
        return self.to_string() == other.to_string()

    def __ne__(self, other):
        return not(self == other)
    
    def __lt__(self, other):
        return self.to_string() < other.to_string()