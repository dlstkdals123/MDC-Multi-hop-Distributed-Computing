class Performance:
    """
    노드의 성능 정보를 저장하는 클래스입니다.

    Attributes:
        _input (float): 입력량 (KB/s)
        _output (float): 출력량 (KB/s)
        _computing (float): 계산량 (GFLOPs/s)
    """
    def __init__(self, input: float, output: float, computing: float):
        self._input = input
        self._output = output
        self._computing = computing

    @property
    def input(self) -> float:
        return self._input
    
    @property
    def output(self) -> float:
        return self._output
    
    @property
    def computing(self) -> float:
        return self._computing

    @input.setter
    def input(self, input: float) -> None:
        self._input = input
    
    @output.setter
    def output(self, output: float) -> None:
        self._output = output
    
    @computing.setter
    def computing(self, computing: float) -> None:
        self._computing = computing