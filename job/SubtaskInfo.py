from job import JobInfo
from layeredgraph import LayerNode, LayerNodePair

# info class for making subtask
class SubtaskInfo(JobInfo):
    def __init__(self, job_info: JobInfo, source_layer_node: LayerNode, destination_layer_node: LayerNode, future_destination_layer_node: LayerNode):
        self._source_layer_node = source_layer_node
        self._destination_layer_node = destination_layer_node
        self._future_destination_layer_node = future_destination_layer_node

        super().__init__(job_info.get_job_id(), job_info.get_terminal_destination(), job_info.get_job_type(), job_info.get_job_name(), job_info.get_start_time(), job_info.get_input_size())
    
    def get_source(self):
        return self._source_layer_node
    
    def get_destination(self):
        return self._destination_layer_node  
        
    def get_subtask_id(self):
        return self._delimeter.join([self.get_job_id(), self._source_layer_node.to_string(), self._destination_layer_node.to_string()]) # yolo20240312101010_192.168.1.5-0_192.168.1.6-0_1
    
    def set_next_subtask_id(self):
        self._source_layer_node = self._destination_layer_node
        self._destination_layer_node = self._future_destination_layer_node
        
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