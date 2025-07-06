from job import JobInfo
from layeredgraph import LayerNode, LayerNodePair
from typing import List, Tuple
class SubtaskInfo(JobInfo):
    def __init__(self, job_info: JobInfo, path: List[Tuple[LayerNode, LayerNode, str]]):
        self._path = path
        self._index = 0
        super().__init__(job_info.get_job_id(), job_info.get_terminal_destination(), job_info.get_job_type(), job_info.get_job_name(), job_info.get_start_time(), job_info.get_input_size())
    
    def get_path(self):
        return self._path

    def get_next_subtask(self):
        if self._index == len(self._path) - 1:
            return None
        else:
            self._index += 1
            return self._path[self._index]

    def get_current_subtask(self):
        return self._path[self._index]
    
    def get_model_name(self):
        return self._path[self._index][2]
    
    def get_source(self):
        return self._path[self._index][0]
    
    def get_destination(self):
        return self._path[self._index][1]  
        
    def get_subtask_id(self):
        return self._delimeter.join([self.get_job_id(), self._path[self._index][0].to_string(), self._path[self._index][1].to_string()]) # yolo20240312101010_192.168.1.5-0_192.168.1.6-0_1
    
    def set_next_subtask_id(self):
        self._index += 1
        
    def get_link(self):
        return LayerNodePair(self._path[self._index][0], self._path[self._index][1])
    
    def is_transmission(self):
        return not self.is_computing()
    
    def is_computing(self):
        return self._path[self._index][0].is_same_node(self._path[self._index][1])

    def get_computing_ratio(self):
        return self._path[self._index][0].get_model_names()[self._path[self._index][2]].get_computing_ratio() if self.is_computing() else 0.0
    
    def get_transfer_ratio(self):
        return self._path[self._index][0].get_model_names()[self._path[self._index][2]].get_transfer_ratio() if self.is_transmission() else 0.0
    
    def __hash__(self):
        return hash(self.get_subtask_id())
    
    def __str__(self):
        return self.get_subtask_id()
    
    def __repr__(self):
        return self.get_subtask_id()

    def __eq__(self, other):
        return self.get_subtask_id() == other.get_subtask_id()

    def __ne__(self, other):
        return not(self == other)