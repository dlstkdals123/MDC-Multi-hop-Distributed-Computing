from job import JobInfo
from layeredgraph import LayerNode, LayerNodePair
from typing import List, Tuple
class SubtaskInfo(JobInfo):
    """
    서브태스크의 정보를 저장하는 클래스입니다.

    Attributes:
        _source_layer_node (LayerNode): 서브태스크의 소스 노드.
        _destination_layer_node (LayerNode): 서브태스크의 목적지 노드.
        _model_name (str): 서브태스크의 마지막으로 사용한 모델 이름.
        _primary_path_index (int): 서브태스크의 주요 경로 인덱스.
        _terminal_index (int): 서브태스크의 종착지 인덱스.
    """
    def __init__(self, job_info: JobInfo, source_layer_node: LayerNode, destination_layer_node: LayerNode, model_name: str = None, primary_path_index: int = 0, terminal_index: int = 0):
        self._source_layer_node = source_layer_node
        self._destination_layer_node = destination_layer_node
        self._model_name = model_name
        self._primary_path_index = primary_path_index
        self._terminal_index = terminal_index
        super().__init__(job_info.job_name, job_info.job_type, job_info.input_bytes, job_info.source_ip, job_info.terminal_destination, job_info.start_time)
    
    @property
    def source(self) -> LayerNode:
        return self._source_layer_node
    
    @property
    def destination(self) -> LayerNode:
        return self._destination_layer_node
    
    @property
    def model_name(self) -> str:
        return self._model_name
        
    def get_subtask_id(self) -> str:
        return self._delimeter.join([self.job_id, self._source_layer_node.to_string(), str(self._primary_path_index)])

    def get_link(self) -> LayerNodePair:
        return LayerNodePair(self._source_layer_node, self._destination_layer_node)
    
    def set_next_source(self):
        if self._primary_path_index < self._terminal_index:
            self._source_layer_node = self._destination_layer_node
            self._primary_path_index += 1
    
    def is_computing(self) -> bool:
        return self._source_layer_node.is_same_node(self._destination_layer_node)

    def is_transmission(self) -> bool:
        return not self.is_computing()
    
    def is_terminated(self) -> bool:
        return self._primary_path_index == self._terminal_index
    
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