import psutil
import time

NANO_SECOND = 1_000_000_000
KB_PER_BYTE = 1024

class PerformanceManager:
    """
    노드의 계산량과 전송량을 모니터링하고 관리하는 클래스입니다.

    Attributes:
        _last_sent (float): 마지막 전송량 (KB).
        _last_transfer_time (float): 마지막 전송 시간 (ns).

        _alpha (float): EMA 가중치
        _transfer_performance (float): 전송량 (KB/s)
        _computing_performance (float): 계산량 (GFLOPs/s)
    """
    def __init__(self):
        self._last_sent: float = psutil.net_io_counters().bytes_sent / KB_PER_BYTE
        self._last_transfer_time: float = time.time() * NANO_SECOND

        self._alpha: float = 0.9
        self._transfer_performance: float = 0
        self._computing_performance: float = 0

    def update_transfer_performance(self) -> None:
        transfer_performance = self._check_and_get_current_transfer_performance()
        
        self._transfer_performance = self._alpha * self._transfer_performance + (1 - self._alpha) * transfer_performance

    def _check_and_get_current_transfer_performance(self) -> float:
        cur_sent = psutil.net_io_counters().bytes_sent / KB_PER_BYTE
        cur_time = time.time() * NANO_SECOND

        # KB/s
        sent_delta = (cur_sent - self._last_sent) / (cur_time - self._last_transfer_time) if cur_time - self._last_transfer_time > 0 else 0
        sent_delta *= NANO_SECOND

        self._last_sent = cur_sent
        self._last_transfer_time = cur_time

        return sent_delta

    def update_computing_performance(self, computing_performance: float) -> None:
        self._computing_performance = self._alpha * self._computing_performance + (1 - self._alpha) * computing_performance

    @property
    def computing_performance(self) -> float:
        return self._computing_performance
    
    @property
    def transfer_performance(self) -> float:
        return self._transfer_performance