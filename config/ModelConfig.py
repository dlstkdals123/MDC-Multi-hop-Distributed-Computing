from typing import Dict

class ModelConfig:
    """
    Model 설정 정보를 저장하는 클래스입니다.

    Attributes:
        _warmup (bool): 모델 워밍업 여부
        _warmup_input (List[int]): 모델 워밍업 입력 크기
        _computing_ratio (float): 모델 계산 비율
        _transfer_ratio (float): 모델 전송 비율
    """

    def __init__(self, model_config: Dict[str, any]):
        """
        Args:
            model_config (Dict[str, any]): 모델 설정 정보가 담긴 Json 형식의 딕셔너리.
        """
        self.check_validate(model_config)

        self._warmup = model_config["warmup"]
        self._warmup_input = model_config["warmup_input"]
        self._computing_ratio = model_config["computing_ratio"]
        self._transfer_ratio = model_config["transfer_ratio"]

    def check_validate(self, model_config: Dict[str, any]):
        """
        config.json의 Model 정보가 올바른지 검증합니다.
        
        Raises:
            ValueError: 필수 정보가 누락되었을 때 발생합니다.
            필수 정보는 매뉴얼을 참고해주세요.
        """
        required_keys = ["warmup", "computing_ratio", "transfer_ratio"]

        for key in required_keys:
            if key not in model_config:
                raise ValueError(f"Missing required key: {key}")
        
        # warmup이 True인 경우 warmup_input이 반드시 있어야 함
        if key == "warmup" and model_config[key] == "True" and "warmup_input" not in model_config:
            raise ValueError(f"Missing required key: warmup_input")
        
        # computing_ratio의 값이 0보다 크거나 같아야 함
        if model_config["computing_ratio"] < 0:
            raise ValueError(f"computing_ratio must be greater than or equal to 0")
        
    def get_warmup(self):
        return self._warmup
    
    def get_warmup_input(self):
        return self._warmup_input
    
    def get_computing_ratio(self):
        return self._computing_ratio
    
    def get_transfer_ratio(self):
        return self._transfer_ratio