from typing import List

import psutil
import time

class CapacityManager:
    """
    노드의 계산량과 전송량을 모니터링하고 관리하는 클래스입니다.

    Attributes:
        _sample_num (int): 샘플링할 데이터 개수.
        _last_sent (int): 마지막 전송량 (KB).
        _last_transfer_time (float): 마지막 전송 시간 (s).
        _computing_count (int): 계산량 업데이트 횟수.
        _computing_capacity_avg (float): 계산량 평균 (GFLOPs/s).
        _transfer_count (int): 전송량 업데이트 횟수.
        _transfer_capacity_avg (float): 전송량 평균 (KB/s).
    """
    def __init__(self):

        self._sample_num: int = 100

        self._last_sent: int = psutil.net_io_counters().bytes_sent / 1024
        self._last_transfer_time: float = time.time()

        self._transfer_count: int = 0
        self._transfer_capacity_avg: float = 0
        
        self._computing_count: int = 0
        self._computing_capacity_avg: float = 0

    def update_transfer_capacity(self) -> None:
        transfer_capacity = self._check_and_get_current_transfer_capacity()
        
        self._transfer_count += 1
        
        # 증분 평균 계산
        effective_n = min(self._transfer_count, self._sample_num)
        self._transfer_capacity_avg = self._transfer_capacity_avg + (transfer_capacity - self._transfer_capacity_avg) / effective_n

    def _check_and_get_current_transfer_capacity(self) -> float:
        cur_sent = psutil.net_io_counters().bytes_sent / 1024
        cur_time = time.time()

        sent_delta = (cur_sent - self._last_sent) / (cur_time - self._last_transfer_time) if cur_time - self._last_transfer_time > 0 else 0

        self._last_sent = cur_sent
        self._last_transfer_time = cur_time

        return sent_delta

    def update_computing_capacity(self, computing_capacity: float) -> None:
        self._computing_count += 1
        
        # 증분 평균 계산
        effective_n = min(self._computing_count, self._sample_num)
        self._computing_capacity_avg = self._computing_capacity_avg + (computing_capacity - self._computing_capacity_avg) / effective_n

    def get_computing_capacity_avg(self) -> float:
        return self._computing_capacity_avg
    
    def get_transfer_capacity_avg(self) -> float:
        return self._transfer_capacity_avg