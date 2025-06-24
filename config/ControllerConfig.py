from typing import Dict

class ControllerConfig:
    """
    Controller 설정 정보를 저장하는 클래스입니다.

    Attributes:
        _controller_config (Dict[str, any]): 컨트롤러 설정 정보가 담긴 Json 형식의 딕셔너리.
        _experiment_name (str): 실험 이름
        _sync_time (int): 동기화 시간.
    """
        
    def __init__(self, controller_config: Dict[str, any]):
        """
        Args:
            controller_config (Dict[str, any]): 컨트롤러 설정 정보가 담긴 Json 형식의 딕셔너리.
        """
        self.check_validate(controller_config)

        self._controller_config = controller_config

        self._experiment_name = self._controller_config["experiment_name"]
        self._sync_time = self._controller_config["sync_time"]

    def check_validate(self, controller_config: Dict[str, any]):
        """
        config.json의 Controller 정보가 올바른지 검증합니다.
        
        Raises:
            ValueError: 필수 정보가 누락되었을 때 발생합니다.
            필수 정보는 매뉴얼을 참고해주세요.
        """
        required_keys = ["experiment_name", "sync_time"]

        for key in required_keys:
            if key not in controller_config:
                raise ValueError(f"Missing required key: {key}")
            
    def get_experiment_name(self):
        return self._experiment_name
    
    def get_sync_time(self):
        return self._sync_time