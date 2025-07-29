import psutil
import time
from communication.Performance import Performance

NANO_SECOND = 1_000_000_000
KB_PER_BYTE = 1024

class PerformanceManager:
    """
    노드의 계산량과 전송량을 모니터링하고 관리하는 클래스입니다.

    Attributes:
        _last_input (float): 마지막 입력량 (KB).
        _last_output (float): 마지막 출력량 (KB).
        _last_transfer_time (float): 마지막 전송 시간 (ns).

        _alpha (float): EMA 가중치
        _performance (Performance): 노드의 성능 정보
    """
    def __init__(self):
        self._net_io_counters = psutil.net_io_counters()
        self._last_input: float = self._net_io_counters.bytes_recv / KB_PER_BYTE # KB/s
        self._last_output: float = self._net_io_counters.bytes_sent / KB_PER_BYTE # KB/s
        self._last_dropped_input: float = self._net_io_counters.dropin # packet/s
        self._last_dropped_output: float = self._net_io_counters.dropout # packet/s
        self._last_transfer_time: float = time.time() * NANO_SECOND

        self._alpha: float = 0.9
        self._performance: Performance = Performance(0, 0, 0, 0, 0)

    def update_transfer_performance(self) -> None:
        net_io_counters = psutil.net_io_counters()
        cur_input = net_io_counters.bytes_recv / KB_PER_BYTE # KB/s
        cur_output = net_io_counters.bytes_sent / KB_PER_BYTE # KB/s
        cur_dropped_input = net_io_counters.dropin # packet/s
        cur_dropped_output = net_io_counters.dropout # packet/s
        cur_time = time.time() * NANO_SECOND

        # KB/s
        input_delta = (cur_input - self._last_input) / (cur_time - self._last_transfer_time) if cur_time - self._last_transfer_time > 0 else 0
        input_delta *= NANO_SECOND

        output_delta = (cur_output - self._last_output) / (cur_time - self._last_transfer_time) if cur_time - self._last_transfer_time > 0 else 0
        output_delta *= NANO_SECOND

        # packet/s
        dropped_input_delta = (cur_dropped_input - self._last_dropped_input) / (cur_time - self._last_transfer_time) if cur_time - self._last_transfer_time > 0 else 0
        dropped_output_delta = (cur_dropped_output - self._last_dropped_output) / (cur_time - self._last_transfer_time) if cur_time - self._last_transfer_time > 0 else 0

        self._performance.input = input_delta
        self._performance.output = output_delta
        self._performance.dropped_input = dropped_input_delta
        self._performance.dropped_output = dropped_output_delta

        self._last_input = cur_input
        self._last_output = cur_output
        self._last_dropped_input = cur_dropped_input
        self._last_dropped_output = cur_dropped_output
        self._last_transfer_time = cur_time

    def update_computing_performance(self, computing_performance: float) -> None:
        self._performance.computing = self._alpha * self._performance.computing + (1 - self._alpha) * computing_performance

    def get_performance(self) -> Performance:
        return self._performance
    