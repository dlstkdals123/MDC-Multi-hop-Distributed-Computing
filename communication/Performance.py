class Performance:
    """
    노드의 성능 정보를 저장하는 클래스입니다.

    Attributes:
        _actual_queue_backlog (float): 실제 큐 백로그 (KB/s)
        _input (float): 입력량 (KB/s)
        _output (float): 출력량 (KB/s)
        _computing (float): 계산량 (GFLOPs/s)
    """

    def __init__(self, actual_queue_backlog: float, input: float, output: float, computing: float):
        self._actual_queue_backlog = actual_queue_backlog
        self._input = input
        self._output = output
        self._computing = computing

    def is_empty(self) -> bool:
        return self._actual_queue_backlog == 0 and self._input == 0 and self._output == 0 and self._computing == 0

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
    