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
        _last_dropped_input (float): 마지막 입력 패킷 드롭량 (packet).
        _last_dropped_output (float): 마지막 출력 패킷 드롭량 (packet).

        _performance (Performance): 노드의 성능 정보
    """
    def __init__(self):
        self._net_io_counters = psutil.net_io_counters()
        self._last_input: float = self._net_io_counters.bytes_recv / KB_PER_BYTE # KB
        self._last_output: float = self._net_io_counters.bytes_sent / KB_PER_BYTE # KB
        self._last_dropped_input: float = self._net_io_counters.dropin # packet
        self._last_dropped_output: float = self._net_io_counters.dropout # packet
        
        self._computing: float = 0 # GFLOPs
        
        self._performance: Performance = Performance(0, 0, 0, 0)

    def update_performance(self) -> None:
        cur_input = self._net_io_counters.bytes_recv / KB_PER_BYTE
        cur_output = self._net_io_counters.bytes_sent / KB_PER_BYTE
        cur_dropped_input = self._net_io_counters.dropin
        cur_dropped_output = self._net_io_counters.dropout
        cur_actual_queue_backlog = self._performance.actual_queue_backlog

        input_delta = cur_input - self._last_input
        output_delta = cur_output - self._last_output
        dropped_input_delta = cur_dropped_input - self._last_dropped_input
        dropped_output_delta = cur_dropped_output - self._last_dropped_output

        self._performance.actual_queue_backlog = max(cur_actual_queue_backlog - output_delta, 0) + input_delta
        self._performance.dropped_input = dropped_input_delta
        self._performance.dropped_output = dropped_output_delta
        self._performance.computing = self._computing

        self._last_input = cur_input
        self._last_output = cur_output
        self._last_dropped_input = cur_dropped_input
        self._last_dropped_output = cur_dropped_output
        self._computing = 0

    def add_computing(self, computing: float) -> None:
        self._computing += computing

    @property
    def performance(self) -> Performance:
        return self._performance
    