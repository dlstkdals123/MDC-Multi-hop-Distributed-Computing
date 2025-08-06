from typing import Dict

class SenderConfig:
    """
    Sender 설정 정보를 저장하는 클래스입니다.

    Attributes:
        _frame_delay (float): 프레임 지연 시간. (sec)
    """
    def __init__(self, sender_config: Dict[str, any]):
        """
        Args:
            sender_config (Dict[str, any]): Sender 설정 정보가 담긴 Json 형식의 딕셔너리.
        """
        self._check_validate(sender_config)

        self._frame_delay: float = float(sender_config["frame_delay"])

    def _check_validate(self, sender_config: Dict[str, any]):
        """
        config.json의 Sender 정보가 올바른지 검증합니다.
        
        Raises:
            ValueError: 필수 정보가 누락되었을 때 발생합니다.
        """
        required_keys = ["frame_delay"]
        for key in required_keys:
            if key not in sender_config:
                raise ValueError(f"Missing required key: {key}")

    @property
    def frame_delay(self) -> float:
        return self._frame_delay