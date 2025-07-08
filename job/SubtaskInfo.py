from job import JobInfo
from layeredgraph import LayerNode, LayerNodePair
from typing import List, Tuple
class SubtaskInfo(JobInfo):
    def __init__(self, job_info: JobInfo, source_layer_node: LayerNode, destination_layer_node: LayerNode, model_name: str = None, primary_path_index: int = 0):
        self._source_layer_node = source_layer_node
        self._destination_layer_node = destination_layer_node
        self._model_name = model_name
        self._primary_path_index = primary_path_index
        super().__init__(job_info.get_job_id(), job_info.get_terminal_destination(), job_info.get_job_type(), job_info.get_job_name(), job_info.get_start_time(), job_info.get_input_size())
    
    def get_source(self):
        return self._source_layer_node
    
    def get_destination(self):
        return self._destination_layer_node
    
    def get_model_name(self):
        return self._model_name
        
    def get_subtask_id(self):
        return self._delimeter.join([self.get_job_id(), self._source_layer_node.to_string(), str(self._primary_path_index)])
    
    def set_next_source(self):
        self._source_layer_node = self._destination_layer_node
        self._primary_path_index += 1
    
    def get_link(self):
        return LayerNodePair(self._source_layer_node, self._destination_layer_node)
    
    def is_transmission(self):
        return not self.is_computing()
    
    def is_computing(self):
        return self._source_layer_node.is_same_node(self._destination_layer_node)
    
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