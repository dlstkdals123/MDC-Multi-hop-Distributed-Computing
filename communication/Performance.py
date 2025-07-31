class Performance:
    """
    노드의 성능 정보를 저장하는 클래스입니다.

    Attributes:
        _actual_queue_backlog (float): 실제 큐 백로그 (KB/s)
        _input (float): 입력 패킷량 (KB/s)
        _output (float): 출력 패킷량 (KB/s)
        _computing (float): 계산량 (GFLOPs/s)
        _dropped_input (float): 입력 패킷 드롭량 (packet/s)
        _dropped_output (float): 출력 패킷 드롭량 (packet/s)
    """

    def __init__(self, actual_queue_backlog: float, computing: float, dropped_input: float, dropped_output: float):
        self._actual_queue_backlog = actual_queue_backlog
        self._input = 0
        self._output = 0
        self._computing = computing
        self._dropped_input = dropped_input
        self._dropped_output = dropped_output

    @property
    def actual_queue_backlog(self) -> float:
        return self._actual_queue_backlog
    
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

    @actual_queue_backlog.setter
    def actual_queue_backlog(self, actual_queue_backlog: float) -> None:
        self._actual_queue_backlog = actual_queue_backlog
    
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