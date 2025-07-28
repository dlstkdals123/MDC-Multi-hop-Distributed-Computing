import psutil
import time

MS_PER_SECOND = 1_000
KB_PER_BYTE = 1024

class PerformanceManager:
    """
    노드의 계산량과 전송량을 모니터링하고 관리하는 클래스입니다.

    Attributes:
        _last_sent (float): 마지막 전송량 (KB).
        _last_transfer_time (float): 마지막 전송 시간 (ms).

        _alpha (float): EMA 가중치
        _transfer_capacity (float): 전송량 (KB/ms)
        _computing_capacity (float): 계산량 (GFLOPs/ms)
    """
    def __init__(self):
        self._last_sent: float = psutil.net_io_counters().bytes_sent / KB_PER_BYTE
        self._last_transfer_time: float = time.time() * MS_PER_SECOND # ms

        self._alpha: float = 0.9
        self._transfer_capacity: float = 0
        self._computing_capacity: float = 0

    def update_transfer_capacity(self) -> None:
        transfer_capacity = self._check_and_get_current_transfer_capacity()
        
        self._transfer_capacity = self._alpha * self._transfer_capacity + (1 - self._alpha) * transfer_capacity

    def _check_and_get_current_transfer_capacity(self) -> float:
        cur_sent = psutil.net_io_counters().bytes_sent / KB_PER_BYTE
        cur_time = time.time() * MS_PER_SECOND # ms

        sent_delta = (cur_sent - self._last_sent) / (cur_time - self._last_transfer_time) if cur_time - self._last_transfer_time > 0 else 0

        self._last_sent = cur_sent
        self._last_transfer_time = cur_time

        return sent_delta

    def update_computing_capacity(self, computing_capacity: float) -> None:
        self._computing_capacity = self._alpha * self._computing_capacity + (1 - self._alpha) * computing_capacity

    @property
    def computing_capacity(self) -> float:
        return self._computing_capacity
    
    @property
    def transfer_capacity(self) -> float:
        return self._transfer_capacity