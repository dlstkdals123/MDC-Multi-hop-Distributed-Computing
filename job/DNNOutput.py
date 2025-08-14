import torch

from job import SubtaskInfo

class DNNOutput:
    """
    모델의 출력을 저장하는 클래스입니다.

    Attributes:
        _input (torch.Tensor): 모델의 입력.
        _output (torch.Tensor): 모델의 출력.
        _subtask_info (SubtaskInfo): 서브태스크 정보.
    """
    def __init__(self, input: torch.Tensor, subtask_info: SubtaskInfo, size: float = 0) -> None:
        self._input = input
        self._output = dict()
        self._subtask_info = subtask_info
        self._size = size # KB

    def add_output(self, model_name: str, output: torch.Tensor) -> None:
        self._output[model_name] = output

    @property
    def subtask_info(self) -> SubtaskInfo:
        return self._subtask_info

    @property
    def input(self) -> torch.Tensor:
        return self._input

    @property
    def size(self) -> float:
        return self._size

    @subtask_info.setter
    def subtask_info(self, subtask_info: SubtaskInfo):
        self._subtask_info = subtask_info
    
    @size.setter
    def size(self, size: float):
        self._size = size

    def __str__(self):
        return f"DNNOutput(subtask_info={self.subtask_info})" 
        
    def __eq__(self, other):
        return self.subtask_info.get_subtask_id() == other.subtask_info.get_subtask_id()
    
    def __hash__(self):
        return hash(self.subtask_info.get_subtask_id())