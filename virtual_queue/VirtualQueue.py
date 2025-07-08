from typing import Tuple, Dict
from job import DNNSubtask, SubtaskInfo

import threading
try:
    from time import time_ns
except ImportError:
    from datetime import datetime
    # For compatibility with Python 3.6
    def time_ns():
        now = datetime.now()
        return int(now.timestamp() * 1e9)

class VirtualQueue:
    def __init__(self):
        self.subtask_infos: Dict[SubtaskInfo, Tuple[DNNSubtask, int]] = dict()
        self.mutex = threading.Lock()

    def garbage_subtask_collector(self, collect_garbage_job_time: int):
        cur_time = time_ns()
        self.mutex.acquire()
        keys_to_delete = [subtask_info for subtask_info, (dnn_subtask, start_time_nano) in self.subtask_infos.items() if cur_time - start_time_nano >= collect_garbage_job_time * 1_000_000_000]

        for k in keys_to_delete:
            del self.subtask_infos[k]

        print(f"Deleted {len(keys_to_delete)} jobs. {len(self.subtask_infos)} remains.")

        self.mutex.release()

    def exist_subtask_info(self, subtask_info: SubtaskInfo):
        self.mutex.acquire()
        result = subtask_info in self.subtask_infos
        self.mutex.release()
        return result

    def add_subtask_info(self, subtask_info: SubtaskInfo, subtask: DNNSubtask):
        # ex) "192.168.1.5", Job
        if self.exist_subtask_info(subtask_info):
            return False
        
        else:
            cur_time = time_ns()
            self.subtask_infos[subtask_info] = (subtask, cur_time)
            return True

    def get_subtask_info(self, subtask_info: SubtaskInfo):
        self.mutex.acquire()
        subtask, _ = self.subtask_infos[subtask_info]
        self.mutex.release()
        return subtask.get_subtask_info()

    def del_subtask_info(self, subtask_info):
        self.mutex.acquire()
        del self.subtask_infos[subtask_info]
        self.mutex.release()
    
    def find_subtask_info(self, subtask_info):
        if self.exist_subtask_info(subtask_info):
            self.mutex.acquire()
            subtask, _ = self.subtask_infos[subtask_info]
            self.mutex.release()
            return subtask
        else:
            raise Exception("No flow subtask_infos : ", subtask_info)
        
    def pop_subtask_info(self, subtask_info):
        subtask = self.find_subtask_info(subtask_info)
        self.del_subtask_info(subtask_info)

        return subtask
    
    def get_backlogs(self):
        links = {}
        self.mutex.acquire()
        for subtask_info, (subtask, _) in self.subtask_infos.items():
            subtask: DNNSubtask

            link = subtask_info.get_link()

            if link in links:
                links[link] += subtask.get_backlog()
            else:
                links[link] = subtask.get_backlog()

        self.mutex.release()

        return links
        
    def __str__(self):
        return str(self.subtask_infos)