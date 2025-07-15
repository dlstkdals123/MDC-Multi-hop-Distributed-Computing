class RequestConfig:
    """
    설정 정보를 요청하는 클래스입니다.

    Attributes:
        _ip (str): 노드의 IP 주소.
    """
    def __init__(self, ip: str):
        self._check_validate(ip)
        self._ip: str = ip

    def _check_validate(self, ip: str):
        """
        IP 주소가 올바른지 검증합니다.
        """
        if not ip:
            raise ValueError("IP 주소는 빈 문자열이 될 수 없습니다.")

    @property
    def ip(self) -> str:
        return self._ip