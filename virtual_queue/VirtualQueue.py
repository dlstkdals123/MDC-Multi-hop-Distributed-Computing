from typing import Tuple, Dict
from job import DNNSubtask, SubtaskInfo
from communication import Performance
from layeredgraph import LayerNodePair

import threading
import time

NANO_SECOND = 1_000_000_000

class VirtualQueue:
    def __init__(self):
        self.subtask_infos: Dict[SubtaskInfo, Tuple[DNNSubtask, int]] = dict()
        self._last_computing_capacity: float = 0
        self._last_transfer_capacity: float = 0
        self._last_subtask_info: SubtaskInfo = None
        self._last_update_time: float = time.time() * NANO_SECOND
        self.mutex = threading.Lock()

    def garbage_subtask_collector(self, collect_garbage_job_time: int):
        cur_time = time.time() * NANO_SECOND # ns
        self._last_update_time = cur_time

        self.mutex.acquire()
        keys_to_delete = [subtask_info for subtask_info, (dnn_subtask, start_time_nano) in self.subtask_infos.items() if cur_time - start_time_nano >= collect_garbage_job_time * NANO_SECOND]

        for k in keys_to_delete:
            del self.subtask_infos[k]
        self.mutex.release()

        print(f"Deleted {len(keys_to_delete)} jobs. {len(self.subtask_infos)} remains.")

    def update_backlog(self, performance: Performance):
        cur_time = time.time() * NANO_SECOND # ns
        time_delta = cur_time - self._last_update_time
        time_delta /= NANO_SECOND # s

        self._last_computing_capacity += performance.computing * time_delta # GFLOPs (GFLOPs/s * s)
        self._last_transfer_capacity += performance.output * time_delta # KB (KB/s * s)

        print(f"Last computing capacity: {self._last_computing_capacity}, Last transfer capacity: {self._last_transfer_capacity}")

        self._last_update_time = cur_time

    def exist_subtask_info(self, subtask_info: SubtaskInfo):
        self.mutex.acquire()
        result = subtask_info in self.subtask_infos
        self.mutex.release()
        return result

    def add_subtask_info(self, subtask_info: SubtaskInfo, subtask: DNNSubtask):
        # ex) "192.168.1.5", Job
        self.mutex.acquire()
        if subtask_info in self.subtask_infos:
            self.mutex.release()
            return False
        else:
            cur_time = time.time() * NANO_SECOND # ns
            self.subtask_infos[subtask_info] = (subtask, cur_time)
            self.mutex.release()
            return True

    def get_subtask_info(self, subtask_info: SubtaskInfo):
        self.mutex.acquire()
        subtask, _ = self.subtask_infos[subtask_info]
        self.mutex.release()
        return subtask.subtask_info
    
    def find_subtask_info(self, subtask_info):
        self.mutex.acquire()
        subtask, _ = self.subtask_infos[subtask_info]
        self.mutex.release()
        if subtask is None:
            raise Exception("No flow subtask_infos : ", subtask_info)
        
        return subtask
        
    def pop_subtask_info(self, subtask_info):
        self.mutex.acquire()
        
        subtask, _ = self.subtask_infos[subtask_info]
        self._last_subtask_info = None
        self._last_computing_capacity -= subtask.get_backlog()
        self._last_transfer_capacity -= subtask.get_backlog()

        del self.subtask_infos[subtask_info]

        self.mutex.release()

        return subtask
    
    def get_backlogs(self) -> Dict[LayerNodePair, float]:
        """
        대기중인 서브태스크에 대해서 출발지와 도착지에 대한 백로그 총합을 반환합니다.
        백로그는 서브태스크의 계산량 또는 전송량을 의미합니다.

        Returns:
            Dict[LayerNodePair, float]: 대기중인 서브태스크의 백로그 총합.
        """
        links = {}
        self.mutex.acquire()
        for subtask_info, (subtask, _) in self.subtask_infos.items():
            subtask: DNNSubtask

            link: LayerNodePair = subtask_info.get_link()

            if link in links:
                links[link] += subtask.get_backlog()
            else:
                links[link] = subtask.get_backlog()

        if self._last_subtask_info is not None:
            link: LayerNodePair = self._last_subtask_info.get_link()

            if link in links:
                links[link] -= self._last_computing_capacity
                links[link] -= self._last_transfer_capacity

        links = {link: max(value, 0) for link, value in links.items()}
        self._last_computing_capacity = 0
        self._last_transfer_capacity = 0

        self.mutex.release()

        return links
    
    @property
    def last_subtask_info(self):
        return self._last_subtask_info
    
    @last_subtask_info.setter
    def last_subtask_info(self, subtask_info: SubtaskInfo):
        self._last_subtask_info = subtask_info
        
    def __str__(self):
        return str(self.subtask_infos)