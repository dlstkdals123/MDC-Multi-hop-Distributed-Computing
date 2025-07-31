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
        net_io_counters = psutil.net_io_counters()
        self._last_input: float = net_io_counters.bytes_recv / KB_PER_BYTE # KB
        self._last_output: float = net_io_counters.bytes_sent / KB_PER_BYTE # KB
        self._last_dropped_input: float = net_io_counters.dropin # packet
        self._last_dropped_output: float = net_io_counters.dropout # packet
        self._last_time: float = time.time() * NANO_SECOND # ns
        
        self._alpha: float = 0.9
        self._computing: float = 0 # GFLOPs/s
        
        self._performance: Performance = Performance(0, 0, 0, 0)

    def update_performance(self) -> None:
        # 네트워크 측정
        net_io_counters = psutil.net_io_counters()
        cur_input = net_io_counters.bytes_recv / KB_PER_BYTE
        cur_output = net_io_counters.bytes_sent / KB_PER_BYTE
        cur_dropped_input = net_io_counters.dropin
        cur_dropped_output = net_io_counters.dropout
        cur_actual_queue_backlog = self._performance.actual_queue_backlog
        cur_time = time.time() * NANO_SECOND

        # 네트워크 변화량 계산 (per second)
        time_delta = cur_time - self._last_time

        input_delta = (cur_input - self._last_input) / time_delta
        input_delta *= NANO_SECOND

        output_delta = (cur_output - self._last_output) / time_delta
        output_delta *= NANO_SECOND

        dropped_input_delta = (cur_dropped_input - self._last_dropped_input) / time_delta
        dropped_input_delta *= NANO_SECOND

        dropped_output_delta = (cur_dropped_output - self._last_dropped_output) / time_delta
        dropped_output_delta *= NANO_SECOND

        queue_backlog_delta = (max(cur_actual_queue_backlog - output_delta, 0) + input_delta) / time_delta
        queue_backlog_delta *= NANO_SECOND

        # 성능 정보 갱신
        self._performance.actual_queue_backlog = queue_backlog_delta
        self._performance.input = input_delta
        self._performance.output = output_delta
        self._performance.dropped_input = dropped_input_delta
        self._performance.dropped_output = dropped_output_delta
        self._performance.computing = self._computing

        # 이전 상태 업데이트
        self._last_input = cur_input
        self._last_output = cur_output
        self._last_dropped_input = cur_dropped_input
        self._last_dropped_output = cur_dropped_output
        self._last_time = cur_time

    def update_computing(self, computing: float) -> None:
        self._computing = self._alpha * self._computing + (1 - self._alpha) * computing # GFLOPs/s

    @property
    def performance(self) -> Performance:
        return self._performance
    