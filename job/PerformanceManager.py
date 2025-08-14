import time
from communication.Performance import Performance

NANO_SECOND = 1_000_000_000

class PerformanceManager:
    """
    노드의 계산량과 전송량을 모니터링하고 관리하는 클래스입니다.

    Attributes:
        _last_input (float): 마지막 입력량 (KB).
        _last_output (float): 마지막 출력량 (KB).
        _last_computing (float): 마지막 계산량 (GFLOPs).
        _last_time (float): 마지막 업데이트 시간 (ns).
        _sync_time (float): 동기화 시간 (ns).

        _performance (Performance): 노드의 성능 정보
    """
    def __init__(self, sync_seconds: float = 1.0):
        self._last_input: float = 0 # KB
        self._last_output: float = 0 # KB
        self._last_computing: float = 0 # GFLOPs
        self._last_time: float = time.time() * NANO_SECOND # ns
        self._sync_time: float = sync_seconds * NANO_SECOND # ns

        self._performance: Performance = Performance(0, self._last_input, self._last_output, self._last_computing)

    def add_input(self, kb: float) -> None:
        self._last_input += kb
    
    def add_output(self, kb: float) -> None:
        self._last_output += kb

    def update_computing(self, computing: float) -> None:
        self._last_computing += computing

    def update_performance(self) -> None:
        # 네트워크 측정
        cur_actual_queue_backlog = self._performance.actual_queue_backlog
        cur_time = time.time() * NANO_SECOND

        # 네트워크 변화량 계산 (per second)
        time_delta = cur_time - self._last_time # ns

        # 동기화 시간보다 짧은 시간이 지났을 경우 이전 성능 정보를 고려
        if time_delta < self._sync_time:
            remaining_ratio = (self._sync_time - time_delta) / self._sync_time
            current_ratio = time_delta / self._sync_time

            input_delta = (self._performance.input * remaining_ratio) + (self._last_input / time_delta * NANO_SECOND * current_ratio)
            output_delta = (self._performance.output * remaining_ratio) + (self._last_output / time_delta * NANO_SECOND * current_ratio)
            computing_delta = (self._performance.computing * remaining_ratio) + (self._last_computing / time_delta * NANO_SECOND * current_ratio)
        else:
            input_delta = self._last_input / time_delta * NANO_SECOND
            output_delta = self._last_output / time_delta * NANO_SECOND
            computing_delta = self._last_computing / time_delta * NANO_SECOND

        # total input, output
        time_second = time_delta / NANO_SECOND
        total_output = output_delta * time_second # KB
        total_input = input_delta * time_second # KB

        queue_backlog = (max(cur_actual_queue_backlog - total_output, 0) + total_input) # KB

        # 성능 정보 갱신
        self._performance.actual_queue_backlog = queue_backlog
        self._performance.input = input_delta
        self._performance.output = output_delta
        self._performance.computing = computing_delta
        
        # 이전 상태 업데이트
        self._last_input = 0
        self._last_output = 0
        self._last_computing = 0
        self._last_time = cur_time

    @property
    def performance(self) -> Performance:
        return self._performance