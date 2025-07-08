import torch

from communication import *
from job import SubtaskInfo
from layeredgraph import LayerNode

class DNNOutput:
    def __init__(self, data: torch.Tensor, subtask_info: SubtaskInfo) -> None:
        # output tensor
        self._output = data

        # subtask info
        self._subtask_info = subtask_info
        
        # delimeter
        self._delimeter = "-"

    def get_subtask_info(self):
        return self._subtask_info

    def get_output(self):
        return self._output
        
    def __eq__(self, other):
        return self.get_subtask_info().get_subtask_id() == other.get_subtask_info().get_subtask_id()
    
    def __hash__(self):
        return hash(self.get_subtask_info().get_subtask_id())