from typing import Dict
from layeredgraph.LayerNode import LayerNode

class Performance:
    """
    노드의 성능 정보를 저장하는 클래스입니다.

    Attributes:
        _input (float): 입력량 (KB/s)
        _output (float): 출력량 (KB/s)
        _computing (float): 계산량 (GFLOPs/s)
        _dropped_input (float): 입력 패킷 드롭량 (packet/s)
        _dropped_output (float): 출력 패킷 드롭량 (packet/s)
        _node_latency (Dict[LayerNode, float]): 노드 간 지연 시간 (ms)
    """

    def __init__(self, input: float, output: float, computing: float, dropped_input: float, dropped_output: float, node_latency: Dict[LayerNode, float]):
        self._input = input
        self._output = output
        self._computing = computing
        self._dropped_input = dropped_input
        self._dropped_output = dropped_output
        self._node_latency = node_latency

    @property
    def input(self) -> float:
        return self._input
    
    @property
    def output(self) -> float:
        return self._output
    
    @property
    def computing(self) -> float:
        return self._computing
    
    @property
    def dropped_input(self) -> float:
        return self._dropped_input
    
    @property
    def dropped_output(self) -> float:
        return self._dropped_output

    @property
    def node_latency(self) -> Dict[LayerNode, float]:
        return self._node_latency

    @input.setter
    def input(self, input: float) -> None:
        self._input = input
    
    @output.setter
    def output(self, output: float) -> None:
        self._output = output
    
    @computing.setter
    def computing(self, computing: float) -> None:
        self._computing = computing
    
    @dropped_input.setter
    def dropped_input(self, dropped_input: float) -> None:
        self._dropped_input = dropped_input
    
    @dropped_output.setter
    def dropped_output(self, dropped_output: float) -> None:
        self._dropped_output = dropped_output
    
    @node_latency.setter
    def node_latency(self, node_latency: Dict[LayerNode, float]) -> None:
        self._node_latency = node_latency