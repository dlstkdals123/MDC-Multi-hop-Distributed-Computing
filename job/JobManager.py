from typing import Tuple
import torch

from job import *
from utils import *
from communication import *
from virtual_queue import VirtualQueue, AheadOutputQueue
from config import NetworkConfig, ModelConfig

import threading
import time

try:
    from time import time_ns
except ImportError:
    from datetime import datetime
    # For compatibility with Python 3.6
    def time_ns():
        now = datetime.now()
        return int(now.timestamp() * 1e9)

class JobManager:
    def __init__(self, address, network_config: NetworkConfig, model_config: ModelConfig):
        # TODO
        self._device = "cuda" if torch.cuda.is_available() else "cpu"

        self._network_config = network_config
        self._model_config = model_config
        self._dnn_models = DNNModels(model_config.get_model_names(), model_config, self._device, address)

        self._virtual_queue = VirtualQueue()
        self._ahead_of_time_outputs = AheadOutputQueue()
        
        self.init_garbage_subtask_collector()

    def is_subtask_exists(self, output: DNNOutput) -> bool:
        previous_subtask_info = output.get_subtask_info()
        return bool(self._virtual_queue.exist_subtask_info(previous_subtask_info))
    
    def update_dnn_output(self, dnn_output: DNNOutput):
        previous_subtask_info = dnn_output.get_subtask_info()
        current_subtask_info = self._virtual_queue.get_subtask_info(previous_subtask_info)
        return DNNOutput(dnn_output.get_output(), current_subtask_info)
    
    def is_dnn_output_exists(self, subtask_info: SubtaskInfo) -> bool:
        return bool(self._ahead_of_time_outputs.exist_dnn_output(subtask_info))
        
    # add dnn_output if schedule is not arrived yet
    def pop_dnn_output(self, subtask_info: SubtaskInfo) -> DNNOutput:
        return self._ahead_of_time_outputs.pop_dnn_output(subtask_info)
        
    def init_garbage_subtask_collector(self):
        garbage_subtask_collector_thread = threading.Thread(target=self.garbage_subtask_collector, args=())
        garbage_subtask_collector_thread.start()

        garbage_dnn_output_collector_thread = threading.Thread(target=self.garbage_dnn_output_collector, args=())
        garbage_dnn_output_collector_thread.start()

    def garbage_subtask_collector(self):
        collect_garbage_job_time = self._network_config.collect_garbage_job_time
        while True:
            time.sleep(collect_garbage_job_time)

            self._virtual_queue.garbage_subtask_collector(collect_garbage_job_time)

    def garbage_dnn_output_collector(self):
        collect_garbage_job_time = self._network_config.collect_garbage_job_time
        while True:
            time.sleep(collect_garbage_job_time)

            self._ahead_of_time_outputs.garbage_dnn_output_collector(collect_garbage_job_time)

    def get_backlogs(self):
        return self._virtual_queue.get_backlogs()

    def run(self, output: DNNOutput, is_compressed: bool = False) -> Tuple[DNNOutput, float]:
        if is_compressed:
            job_name = output.get_subtask_info().get_job_name()
            decompressed_shape = tuple(self._network_config.jobs[job_name]["real_input"])
            real_data = torch.rand(decompressed_shape)
            output = DNNOutput(real_data, output.get_subtask_info())

        previous_subtask_info = output.get_subtask_info()
        if previous_subtask_info.get_job_type() == "dnn":
            # get next destination
            subtask: DNNSubtask = self._virtual_queue.pop_subtask_info(previous_subtask_info)

            # get output data == get current subtask's input
            data = output.get_output()

            if isinstance(data, list):
                data = [d.to(self._device) for d in data]
            else:
                data = data.to(self._device)

            start_time = time_ns() / 1_000_000_000 # ns to s

            # run job
            dnn_output = subtask.run(data)

            end_time = time_ns() / 1_000_000_000 # ns to s

            computing_capacity = subtask.get_backlog() / (end_time - start_time + 1e-05) if subtask.get_backlog() > 0 else 0

            return dnn_output, computing_capacity
        
    # add subtask_info based SubtaskInfo
    def add_subtask(self, subtask_info: SubtaskInfo):

        model_name = subtask_info.get_model_name()
        model: torch.nn.Module = self._dnn_models.get_model(model_name) if model_name != "" else None
        computing = self._dnn_models.get_computing(model_name) if subtask_info.is_computing() else 0
        if subtask_info.is_transmission():
            transfer = self._dnn_models.get_transfer(model_name) if model_name != "" else subtask_info.get_input_size()
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
        subtask_info = previous_dnn_output.get_subtask_info()
        success_add_dnn_output = self._ahead_of_time_outputs.add_dnn_output(subtask_info, previous_dnn_output)
        
        if not success_add_dnn_output:
            raise Exception(f"DNNOutput already exists. : {previous_dnn_output.get_subtask_info().get_subtask_id()}")

