class NetworkPerformance:
    """
    네트워크 성능 정보를 저장하는 클래스입니다.

    Attributes:
        _gpu_capacity (float): GPU 사용량.
        _ip (str): 노드의 IP 주소.
    """

    def __init__(self, gpu_capacity: float, ip: str):
        """
        Args:
            gpu_capacity (float): GPU 사용량. 0.0 ~ 1.0 사이의 실수가 보장됩니다.
            ip (str): 노드의 IP 주소.
        """
        self.check_validate(gpu_capacity, ip)
        self._gpu_capacity = gpu_capacity
        self._ip = ip

    def check_validate(self, gpu_capacity: float, ip: str):
        """
        GPU 사용량과 IP 주소가 올바른지 검증합니다.

        Raises:
            ValueError: 필수 정보가 누락되었을 때 발생합니다.
        """
        if gpu_capacity < 0.0 or gpu_capacity > 1.0:
            raise ValueError("GPU 사용량은 0.0 ~ 1.0 사이의 실수여야 합니다.")
        
        if not ip:
            raise ValueError("IP 주소는 빈 문자열이 될 수 없습니다.")

    @property
    def gpu_capacity(self):
        return self._gpu_capacity

    @property
    def ip(self):
        return self._ip