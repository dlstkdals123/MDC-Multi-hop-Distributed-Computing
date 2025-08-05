import time
from communication.Performance import Performance

NANO_SECOND = 1_000_000_000

class PerformanceManager:
    """
    노드의 계산량과 전송량을 모니터링하고 관리하는 클래스입니다.

    Attributes:
        _last_input (float): 마지막 입력량 (KB).
        _last_output (float): 마지막 출력량 (KB).
        _last_computing (float): 마지막 계산량 (GFLOPs/s).
        _last_time (float): 마지막 업데이트 시간 (ns).

        _performance (Performance): 노드의 성능 정보
    """
    def __init__(self):
        self._last_input: float = 0 # KB
        self._last_output: float = 0 # KB
        self._last_time: float = time.time() * NANO_SECOND # ns

        self._alpha: float = 0.9
        self._last_computing: float = 0 # GFLOPs/s
        
        self._performance: Performance = Performance(0, self._last_input, self._last_output, self._last_computing)

    def add_input(self, bytes: float) -> None:
        self._last_input += bytes
    
    def add_output(self, bytes: float) -> None:
        self._last_output += bytes

    def update_computing(self, computing: float) -> None:
        self._last_computing = self._alpha * self._last_computing + (1 - self._alpha) * computing

    def update_performance(self) -> None:
        # 네트워크 측정
        cur_actual_queue_backlog = self._performance.actual_queue_backlog
        cur_time = time.time() * NANO_SECOND

        # 네트워크 변화량 계산 (per second)
        time_delta = cur_time - self._last_time

        input_delta = self._last_input / time_delta
        input_delta *= NANO_SECOND

        output_delta = self._last_output / time_delta
        output_delta *= NANO_SECOND

        queue_backlog_delta = (max(cur_actual_queue_backlog - output_delta, 0) + input_delta) / time_delta
        queue_backlog_delta *= NANO_SECOND

        # 성능 정보 갱신
        self._performance.actual_queue_backlog = queue_backlog_delta
        self._performance.input = input_delta
        self._performance.output = output_delta
        
        # 이전 상태 업데이트
        self._last_input = 0
        self._last_output = 0
        self._last_time = cur_time

    @property
    def performance(self) -> Performance:
        return self._performance
    