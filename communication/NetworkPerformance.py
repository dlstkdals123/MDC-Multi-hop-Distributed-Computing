# info class for response NetworkPerformance
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
        self._gpu_capacity = gpu_capacity
        self._ip = ip

    def get_gpu_capacity(self):
        return self._gpu_capacity
    
    def get_ip(self):
        return self._ip