from typing import Tuple
import torch

from job import *
from utils import *
from communication import *
from virtual_queue import VirtualQueue, AheadOutputQueue
from config import NetworkConfig, ModelConfig
from layeredgraph import LayerNodePair

import threading
import time

class JobManager:
    """
    작업 관리자 클래스입니다.
    서브태스크와 DNNOutput을 저장하고 관리합니다.
    서브태스크는 VirtualQueue에 저장됩니다. 이후에 해당하는 DNNOutput이 도착하면 서브태스크를 실행합니다.
    서브태스크가 도착하지 않은 경우, 미리 도착한 DNNOutput은 AheadOutputQueue에 저장됩니다.
    이후에 해당하는 서브태스크가 도착하면 미리 도착한 DNNOutput을 통해 서브태스크를 실행합니다.

    가비지 컬렉터를 사용하여 주기적으로 쓰레기 서브태스크와 DNNOutput을 제거합니다.

    Attributes:
        _device (str): 모델을 실행하는 노드의 디바이스(cpu, cuda).
        _network_config (NetworkConfig): 네트워크 설정.
        _model_config (ModelConfig): 모델 설정.
        _dnn_models (DNNModels): 모델 모음.
        _virtual_queue (VirtualQueue): 가상큐. 서브태스크를 저장 및 관리.
        _ahead_of_time_outputs (AheadOutputQueue): 대기큐. 미리 도착한 DNNOutput을 저장 및 관리.
    """
    def __init__(self, network_config: NetworkConfig, model_config: ModelConfig):
        self._device = "cuda" if torch.cuda.is_available() else "cpu"

        self._network_config = network_config
        self._model_config = model_config
        self._dnn_models: DNNModels = DNNModels(model_config.get_model_names(), model_config, self._device)

        self._virtual_queue: VirtualQueue = VirtualQueue()
        self._ahead_of_time_outputs: AheadOutputQueue = AheadOutputQueue()
        
        self.init_garbage_subtask_collector()

    def is_subtask_exists(self, output: DNNOutput) -> bool:
        # DNNOutput에 대한 서브태스크가 도착했는 지 여부를 반환합니다.
        previous_subtask_info = output.subtask_info
        return bool(self._virtual_queue.exist_subtask_info(previous_subtask_info))
    
    def is_dnn_output_exists(self, subtask_info: SubtaskInfo) -> bool:
        # SubtaskInfo에 대한 DNNOutput이 도착했는 지 여부를 반환합니다.
        return bool(self._ahead_of_time_outputs.exist_dnn_output(subtask_info))

    def update_dnn_output(self, dnn_output: DNNOutput) -> DNNOutput:
        # 막 도착한 DNNOutput의 서브태스크는 잘못된 목적지와 모델 정보를 가지고 있습니다.
        # 따라서 해당 서브태스크와 똑같은 ID에 대한 서브태스크를 가상큐에서 가져와, DNNOutput을 업데이트합니다.
        previous_subtask_info = dnn_output.subtask_info
        current_subtask_info = self._virtual_queue.get_subtask_info(previous_subtask_info)
        return DNNOutput(dnn_output.output(), current_subtask_info)
        
    def pop_dnn_output(self, subtask_info: SubtaskInfo) -> DNNOutput:
        # 대기큐에서 서브태스크 정보를 기다리고 있는 DNNOutput을 pop합니다.
        return self._ahead_of_time_outputs.pop_dnn_output(subtask_info)

    def get_backlogs(self) -> Dict[LayerNodePair, float]:
        return self._virtual_queue.get_backlogs()
        
    def init_garbage_subtask_collector(self):
        garbage_subtask_collector_thread = threading.Thread(target=self._garbage_subtask_collector, args=())
        garbage_subtask_collector_thread.start()

        garbage_dnn_output_collector_thread = threading.Thread(target=self._garbage_dnn_output_collector, args=())
        garbage_dnn_output_collector_thread.start()

    def _garbage_subtask_collector(self):
        collect_garbage_job_time = self._network_config.collect_garbage_job_time
        while True:
            time.sleep(collect_garbage_job_time)

            self._virtual_queue.garbage_subtask_collector(collect_garbage_job_time)

    def _garbage_dnn_output_collector(self):
        collect_garbage_job_time = self._network_config.collect_garbage_job_time
        while True:
            time.sleep(collect_garbage_job_time)

            self._ahead_of_time_outputs.garbage_dnn_output_collector(collect_garbage_job_time)

    def run(self, output: DNNOutput) -> Tuple[DNNOutput, float]:
        subtask_info = output.subtask_info
        if subtask_info.job_type == "dnn":
            
            subtask: DNNSubtask = self._virtual_queue.pop_subtask_info(subtask_info)

            # 아직 run하지 않은 data이므로 output() == 사용해야 할 input data
            data = output.output()

            if isinstance(data, list):
                data = [d.to(self._device) for d in data]
            else:
                data = data.to(self._device)

            start_time = time.time() * 1_000 # ms

            # run job
            dnn_output = subtask.run(data)

            end_time = time.time() * 1_000 # ms

            computing_capacity = subtask.backlog / (end_time - start_time + 1e-05) if subtask.backlog > 0 else 0

            return dnn_output, computing_capacity
        
    # add subtask_info based SubtaskInfo
    def add_subtask(self, subtask_info: SubtaskInfo):

        model_name = subtask_info.model_name
        model: torch.nn.Module = self._dnn_models.get_model(model_name) if model_name != "" else None
        computing = self._dnn_models.get_computing(model_name) if subtask_info.is_computing() else 0
        if subtask_info.is_transmission():
            transfer = self._dnn_models.get_transfer(model_name) if model_name != "" else subtask_info.input_bytes
        else:
            transfer = 0

        subtask = DNNSubtask(
            subtask_info = subtask_info,
            dnn_model = model,
            computing = computing,
            transfer = transfer
        )

        success_add_subtask_info = self._virtual_queue.add_subtask_info(subtask_info, subtask)
        
        if not success_add_subtask_info:
            raise Exception(f"Subtask already exists. : {subtask_info.get_subtask_id()}")
        
    # add dnn_output if schedule is not arrived yet
    def add_dnn_output(self, previous_dnn_output: DNNOutput):
        subtask_info = previous_dnn_output.subtask_info
        success_add_dnn_output = self._ahead_of_time_outputs.add_dnn_output(subtask_info, previous_dnn_output)
        
        if not success_add_dnn_output:
            raise Exception(f"DNNOutput already exists. : {previous_dnn_output.subtask_info.get_subtask_id()}")

