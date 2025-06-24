class RequestNetworkInfo:
    """
    노드의 정보를 요청하는 클래스입니다.

    Attributes:
        _ip (str): 노드의 IP 주소.
    """
    def __init__(self, ip: str):
        """
        Args:
            ip (str): 노드의 IP 주소.
        """
        self.check_validate(ip)
        self._ip = ip

    def check_validate(self, ip: str):
        """
        IP 주소가 올바른지 검증합니다.

        Raises:
            ValueError: 필수 정보가 누락되었을 때 발생합니다.
        """
        if not ip:
            raise ValueError("IP 주소는 빈 문자열이 될 수 없습니다.")

    def get_ip(self):
        return self._ip