from typing import Dict

class MDCConfig:
    """
    MDC 설정 정보를 저장하는 클래스입니다.

    Attributes:
        _computing_capacity (float): MDC의 컴퓨팅 용량.
        _interface_name (str): MDC의 네트워크 인터페이스 이름.
        _wireless (bool): MDC의 무선 여부.
    """
    def __init__(self, mdc_config: Dict[str, any]):
        self._check_validate(mdc_config)

        self._computing_capacity = mdc_config["computing_capacity"]
        self._interface_name = mdc_config["interface_name"]
        self._wireless = mdc_config["wireless"]
    
    def _check_validate(self, mdc_config: Dict[str, any]):
        required_keys = ["computing_capacity", "interface_name", "wireless"]

        for key in required_keys:
            if key not in mdc_config:
                raise ValueError(f"Missing required key: {key}")

    @property
    def computing_capacity(self) -> float:
        return self._computing_capacity
    
    @property
    def interface_name(self) -> str:
        return self._interface_name
    
    @property
    def wireless(self) -> bool:
        return self._wireless