from typing import Dict

class ModelConfig:
    """
    Model 설정 정보를 저장하는 클래스입니다.

    Attributes:
        _warmup (bool): 모델 워밍업 여부
        _warmup_input (List[int]): 모델 워밍업 입력 크기
        _computing_ratios (List[float]): 모델 계산 비율
        _transfer_ratios (List[float]): 모델 전송 비율
    """

    def __init__(self, model_config: Dict[str, any]):
        """
        Args:
            model_config (Dict[str, any]): 모델 설정 정보가 담긴 Json 형식의 딕셔너리.
        """
        self.check_validate(model_config)

        self._warmup = model_config["warmup"]
        self._warmup_input = model_config["warmup_input"]
        self._computing_ratios = model_config["computing_ratios"]
        self._transfer_ratios = model_config["transfer_ratios"]

    def check_validate(self, model_config: Dict[str, any]):
        """
        config.json의 Model 정보가 올바른지 검증합니다.
        
        Raises:
            ValueError: 필수 정보가 누락되었을 때 발생합니다.
            필수 정보는 매뉴얼을 참고해주세요.
        """
        required_keys = ["warmup", "computing_ratios", "transfer_ratios"]

        for key in required_keys:
            if key not in model_config:
                raise ValueError(f"Missing required key: {key}")
        
        # warmup이 True인 경우 warmup_input이 반드시 있어야 함
        if key == "warmup" and model_config[key] == "True" and "warmup_input" not in model_config:
            raise ValueError(f"Missing required key: warmup_input")
        
        # computing_ratios와 transfer_ratios의 길이가 같아야 함
        if len(model_config["computing_ratios"]) != len(model_config["transfer_ratios"]):
            raise ValueError(f"computing_ratios and transfer_ratios must have the same length")
        
        # computing_ratios와 transfer_ratios의 값이 0보다 크거나 같아야 함
        if any(ratio < 0 for ratio in model_config["computing_ratios"] + model_config["transfer_ratios"]):
            raise ValueError(f"computing_ratios and transfer_ratios must be greater than or equal to 0")
        
    def get_warmup(self):
        return self._warmup
    
    def get_warmup_input(self):
        return self._warmup_input
    
    def get_computing_ratios(self):
        return self._computing_ratios
    
    def get_transfer_ratios(self):
        return self._transfer_ratios