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

MS_PER_SECOND = 1_000

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
        """
        Args:
            output (DNNOutput): 서브태스크가 도착했는 지 확인할 DNNOutput.

        Returns:
            bool: 서브태스크가 도착했는 지 여부.
        """
        previous_subtask_info = output.subtask_info
        return bool(self._virtual_queue.exist_subtask_info(previous_subtask_info))
    
    def is_dnn_output_exists(self, subtask_info: SubtaskInfo) -> bool:
        """
        Args:
            subtask_info (SubtaskInfo): 서브태스크 정보.

        Returns:
            bool: 서브태스크가 도착했는 지 여부.
        """
        return bool(self._ahead_of_time_outputs.exist_dnn_output(subtask_info))

    def update_dnn_output(self, dnn_output: DNNOutput) -> None:
        """
        막 도착한 DNNOutput의 서브태스크는 잘못된 목적지와 모델 정보를 가지고 있습니다.
        따라서 해당 서브태스크와 똑같은 ID에 대한 서브태스크를 가상큐에서 가져와, DNNOutput을 업데이트합니다.

        Args:
            dnn_output (DNNOutput): 업데이트할 DNNOutput.
        """
        previous_subtask_info = dnn_output.subtask_info
        current_subtask_info = self._virtual_queue.get_subtask_info(previous_subtask_info)
        dnn_output.subtask_info = current_subtask_info
        
    def pop_dnn_output(self, subtask_info: SubtaskInfo) -> DNNOutput:
        """
        대기큐에서 서브태스크 정보를 기다리고 있는 DNNOutput을 pop합니다.

        Args:
            subtask_info (SubtaskInfo): 서브태스크 정보.

        Returns:
            DNNOutput: 대기큐에서 pop된 DNNOutput.
        """
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
        """
        서브태스크를 실행하고, 단위 시간당 계산량 또는 전송량을 반환합니다.

        (서브태스크가 계산일 경우 단위 시간당 계산량을 반환합니다. (GFLOPs/ms))
        (서브태스크가 전송일 경우 단위 시간당 전송량을 반환합니다. (KB/ms)))

        Args:
            output (DNNOutput): 실행할 서브태스크의 출력.

        Returns:
            Tuple[DNNOutput, float]: 실행 결과와 단위 시간당 계산량 또는 전송량. (GFLOPs/ms 또는 KB/ms)
        """
        subtask_info = output.subtask_info
        if subtask_info.job_type == "dnn":
            
            subtask: DNNSubtask = self._virtual_queue.pop_subtask_info(subtask_info)

            # 아직 run하지 않은 data이므로 사용해야 할 input data입니다.
            data = output.output

            start_time = time.time() * MS_PER_SECOND # ms

            if isinstance(data, list):
                data = [d.to(self._device) for d in data]
            else:
                data = data.to(self._device)
                
            dnn_output = subtask.run(data)

            end_time = time.time() * MS_PER_SECOND # ms

            # 서브태스크가 계산일 경우 단위 시간당 계산량을 반환합니다. (GFLOPs/ms)
            # 서브태스크가 전송일 경우 단위 시간당 전송량을 반환합니다. (KB/ms)
            capacity = subtask.get_backlog() / (end_time - start_time) if subtask.get_backlog() > 0 and end_time - start_time > 0 else 0

            return dnn_output, capacity
        
    # add subtask_info based SubtaskInfo
    def add_subtask(self, subtask_info: SubtaskInfo) -> None:
        """
        서브태스크를 바탕으로 DNNSubtask 객체를 생성하고, 가상큐에 추가합니다.

        Args:
            subtask_info (SubtaskInfo): 서브태스크 정보.
        """
        model_name = subtask_info.model_name
        model: torch.nn.Module = self._dnn_models.get_model(model_name) if model_name != "" else None
        # computing 이라면 항상 모델이 존재합니다.
        computing_capacity = self._dnn_models.get_computing(model_name) if subtask_info.is_computing() else 0 # GFLOPs
        if subtask_info.is_transmission():
            transfer_capacity = self._dnn_models.get_transfer(model_name) if model_name != "" else subtask_info.input_bytes # KB
        else:
            transfer_capacity = 0

        subtask = DNNSubtask(
            subtask_info = subtask_info,
            dnn_model = model,
            computing_capacity = computing_capacity,
            transfer_capacity = transfer_capacity
        )

        success_add_subtask_info = self._virtual_queue.add_subtask_info(subtask_info, subtask)
        
        if not success_add_subtask_info:
            raise Exception(f"Subtask already exists. : {subtask_info.get_subtask_id()}")
        
    # add dnn_output if schedule is not arrived yet
    def add_dnn_output(self, previous_dnn_output: DNNOutput) -> None:
        """
        미리 도착한 DNNOutput을 대기큐에 추가합니다.

        Args:
            previous_dnn_output (DNNOutput): 대기큐에 추가할 DNNOutput.
        """
        subtask_info = previous_dnn_output.subtask_info
        success_add_dnn_output = self._ahead_of_time_outputs.add_dnn_output(subtask_info, previous_dnn_output)
        
        if not success_add_dnn_output:
            raise Exception(f"DNNOutput already exists. : {previous_dnn_output.subtask_info.get_subtask_id()}")

