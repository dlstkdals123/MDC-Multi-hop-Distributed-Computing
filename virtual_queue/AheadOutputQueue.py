from typing import Tuple, Dict
from job import DNNOutput, SubtaskInfo

import threading
import time

NANO_SECOND = 1_000_000_000

class AheadOutputQueue:
    """
    미리 도착한 DNNOutput을 저장하는 클래스입니다.

    Attributes:
        _dnn_outputs (Dict[SubtaskInfo, Tuple[DNNOutput, int]]): 미리 도착한 DNNOutput을 저장.
    """
    def __init__(self):
        self._dnn_outputs: Dict[SubtaskInfo, Tuple[DNNOutput, int]] = dict()
        self._mutex = threading.Lock()

    def garbage_dnn_output_collector(self, collect_garbage_job_time: int) -> None:
        """
        오래된 DNNOutput을 제거합니다.

        Args:
            collect_garbage_job_time (int): 최대 대기 시간 (s).
        """
        cur_time = time.time() * NANO_SECOND
        with self._mutex:
            keys_to_delete = [subtask_info for subtask_info, (dnn_output, start_time_nano) in self._dnn_outputs.items() if cur_time - start_time_nano >= collect_garbage_job_time * NANO_SECOND]

            for k in keys_to_delete:
                del self._dnn_outputs[k]

            print(f"Deleted {len(keys_to_delete)} outputs. {len(self._dnn_outputs)} remains.")

    def exist_dnn_output(self, subtask_info: SubtaskInfo) -> bool:
        """
        SubtaskInfo을 통해 미리 도착한 DNNOutput이 존재하는지 확인합니다.
        """
        with self._mutex:
            result = subtask_info in self._dnn_outputs
            return result

    def add_dnn_output(self, subtask_info: SubtaskInfo, dnn_output: DNNOutput) -> bool:
        """
        미리 도착한 DNNOutput을 추가합니다.

        Args:
            subtask_info (SubtaskInfo): 서브태스크 정보.
            dnn_output (DNNOutput): 미리 도착한 DNNOutput.
        """
        print(f"ahead dnn output {subtask_info} added.")
        # ex) "192.168.1.5", Job
        with self._mutex:
            if subtask_info in self._dnn_outputs:
                return False
            else:
                cur_time = time.time() * NANO_SECOND
                self._dnn_outputs[subtask_info] = (dnn_output, cur_time)
                return True

    def del_dnn_output(self, subtask_info: SubtaskInfo) -> None:
        with self._mutex:
            del self._dnn_outputs[subtask_info]
        
    def pop_dnn_output(self, subtask_info: SubtaskInfo) -> DNNOutput:
        """
        미리 도착한 DNNOutput을 제거하고, 제거한 DNNOutput을 반환합니다.

        Args:
            subtask_info (SubtaskInfo): 서브태스크 정보.

        Returns:
            DNNOutput: 제거한 DNNOutput.
        """
        print(f"ahead dnn output {subtask_info} poped.")
        with self._mutex:
            if subtask_info in self._dnn_outputs:
                dnn_output, _ = self._dnn_outputs[subtask_info]
                del self._dnn_outputs[subtask_info]
            else:
                raise Exception("No flow dnn_outputs : ", subtask_info)
            return dnn_output
       
    def __str__(self):
        return str(self._dnn_outputs)