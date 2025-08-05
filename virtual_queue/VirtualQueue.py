from typing import Tuple, Dict
from job import DNNSubtask, SubtaskInfo
from communication import Performance
from layeredgraph import LayerNodePair

import threading
import time

NANO_SECOND = 1_000_000_000

class VirtualQueue:
    """
    가상큐를 관리하는 클래스입니다.

    Attributes:
        subtask_infos (Dict[SubtaskInfo, Tuple[DNNSubtask, int]]): 서브태스크 정보와 서브태스크를 저장.
        _last_computing_capacity (float): 마지막 계산 용량. (미사용)
        _last_transfer_capacity (float): 마지막 전송 용량. (미사용)
        _last_subtask_info (SubtaskInfo): 마지막으로 처리된 서브태스크 정보. (미사용)
        _last_update_time (float): 마지막 업데이트 시간 (ns). (미사용)
        mutex (threading.Lock): 스레드 동기화를 위한 뮤텍스.
    """
    def __init__(self):
        self.subtask_infos: Dict[SubtaskInfo, Tuple[DNNSubtask, int]] = dict()
        self._last_computing_capacity: float = 0
        self._last_transfer_capacity: float = 0
        self._last_subtask_info: SubtaskInfo = None
        self._last_update_time: float = time.time() * NANO_SECOND
        self.mutex = threading.Lock()

    def garbage_subtask_collector(self, collect_garbage_job_time: int) -> None:
        """
        오래된 서브태스크를 제거합니다.

        Args:
            collect_garbage_job_time (int): 최대 대기 시간 (s).
        """
        cur_time = time.time() * NANO_SECOND # ns
        self._last_update_time = cur_time

        with self.mutex:
            keys_to_delete = [subtask_info for subtask_info, (dnn_subtask, start_time_nano) in self.subtask_infos.items() if cur_time - start_time_nano >= collect_garbage_job_time * NANO_SECOND]

            for k in keys_to_delete:
                del self.subtask_infos[k]

        print(f"Deleted {len(keys_to_delete)} jobs. {len(self.subtask_infos)} remains.")

    def update_backlog(self, performance: Performance) -> None:
        """
        백로그를 업데이트합니다.
        (미사용)

        Args:
            performance (Performance): 노드의 성능 정보.
        """
        cur_time = time.time() * NANO_SECOND # ns
        time_delta = cur_time - self._last_update_time
        time_delta /= NANO_SECOND # s

        self._last_computing_capacity += performance.computing * time_delta # GFLOPs (GFLOPs/s * s)
        self._last_transfer_capacity += performance.output * time_delta # KB (KB/s * s)

        self._last_update_time = cur_time

    def exist_subtask_info(self, subtask_info: SubtaskInfo) -> bool:
        """
        서브태스크 정보가 존재하는지 확인합니다.

        Args:
            subtask_info (SubtaskInfo): 확인할 서브태스크 정보.

        Returns:
            bool: 서브태스크 정보 존재 여부.
        """
        with self.mutex:
            result = subtask_info in self.subtask_infos
        return result

    def add_subtask_info(self, subtask_info: SubtaskInfo, subtask: DNNSubtask) -> bool:
        """
        서브태스크 정보와 서브태스크를 추가합니다.

        Args:
            subtask_info (SubtaskInfo): 추가할 서브태스크 정보.
            subtask (DNNSubtask): 추가할 서브태스크.

        Returns:
            bool: 추가 성공 여부.
        """
        # ex) "192.168.1.5", Job
        with self.mutex:
            if subtask_info in self.subtask_infos:
                return False
            else:
                cur_time = time.time() * NANO_SECOND # ns
                self.subtask_infos[subtask_info] = (subtask, cur_time)
                return True

    def get_subtask_info(self, subtask_info: SubtaskInfo) -> SubtaskInfo:
        """
        서브태스크 정보를 반환합니다.

        Args:
            subtask_info (SubtaskInfo): 찾을 서브태스크 정보.

        Returns:
            SubtaskInfo: 찾은 서브태스크 정보.
        """
        with self.mutex:
            subtask, _ = self.subtask_infos[subtask_info]
        return subtask.subtask_info
    
    def find_subtask(self, subtask_info: SubtaskInfo) -> DNNSubtask:
        """
        서브태스크를 찾아 반환합니다.

        Args:
            subtask_info (SubtaskInfo): 찾을 서브태스크 정보.

        Returns:
            DNNSubtask: 찾은 서브태스크.

        Raises:
            Exception: 서브태스크를 찾지 못한 경우.
        """
        with self.mutex:
            subtask, _ = self.subtask_infos[subtask_info]
        if subtask is None:
            raise Exception("No flow subtask_infos : ", subtask_info)
        
        return subtask
        
    def pop_subtask_info(self, subtask_info: SubtaskInfo) -> DNNSubtask:
        """
        서브태스크를 제거하고 반환합니다.

        Args:
            subtask_info (SubtaskInfo): 제거할 서브태스크 정보.

        Returns:
            DNNSubtask: 제거된 서브태스크.
        """
        with self.mutex:
            subtask, _ = self.subtask_infos[subtask_info]
            self._last_subtask_info = None
            self._last_computing_capacity -= subtask.get_backlog()
            self._last_transfer_capacity -= subtask.get_backlog()

            del self.subtask_infos[subtask_info]

        return subtask
    
    def get_backlogs(self) -> Dict[LayerNodePair, float]:
        """
        대기중인 서브태스크에 대해서 출발지와 도착지에 대한 백로그 총합을 반환합니다.
        백로그는 서브태스크의 계산량 또는 전송량을 의미합니다.

        Returns:
            Dict[LayerNodePair, float]: 대기중인 서브태스크의 백로그 총합.
        """
        links = {}
        with self.mutex:
            for subtask_info, (subtask, _) in self.subtask_infos.items():
                subtask: DNNSubtask

                link: LayerNodePair = subtask_info.get_link()

                if link in links:
                    links[link] += subtask.get_backlog()
                else:
                    links[link] = subtask.get_backlog()

        return links
    
    @property
    def last_subtask_info(self) -> SubtaskInfo:
        """
        마지막으로 처리된 서브태스크 정보를 반환합니다.

        Returns:
            SubtaskInfo: 마지막으로 처리된 서브태스크 정보.
        """
        return self._last_subtask_info
    
    @last_subtask_info.setter
    def last_subtask_info(self, subtask_info: SubtaskInfo) -> None:
        """
        마지막으로 처리된 서브태스크 정보를 설정합니다.

        Args:
            subtask_info (SubtaskInfo): 설정할 서브태스크 정보.
        """
        self._last_subtask_info = subtask_info
        
    def __str__(self):
        """
        가상큐의 문자열 표현을 반환합니다.

        Returns:
            str: 가상큐의 문자열 표현.
        """
        return str(self.subtask_infos)