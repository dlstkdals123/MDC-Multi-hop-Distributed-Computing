import torch

from job import SubtaskInfo

class DNNOutput:
    """
    모델의 출력을 저장하는 클래스입니다.

    Attributes:
        _output (torch.Tensor): 모델의 출력.
        _subtask_info (SubtaskInfo): 서브태스크 정보.
    """
    def __init__(self, data: torch.Tensor, subtask_info: SubtaskInfo) -> None:
        self._output = data
        self._subtask_info = subtask_info

    @property
    def subtask_info(self) -> SubtaskInfo:
        return self._subtask_info

    @property
    def output(self) -> torch.Tensor:
        return self._output

    @subtask_info.setter
    def subtask_info(self, subtask_info: SubtaskInfo):
        self._subtask_info = subtask_info
        
    def __eq__(self, other):
        return self.subtask_info.get_subtask_id() == other.subtask_info.get_subtask_id()
    
    def __hash__(self):
        return hash(self.subtask_info.get_subtask_id())