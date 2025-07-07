from typing import Dict

class ModelConfig:
    """
    Model 설정 정보를 저장하는 클래스입니다.

    Attributes:
        _model_config (Dict[str, any]): 모델 이름과 모델 설정 정보가 담긴 Json 형식의 딕셔너리.
    """

    def __init__(self, model_configs: Dict[str, any]):
        """
        Args:
            model_configs (Dict[str, any]): 모델 이름과 모델 설정 정보가 담긴 Json 형식의 딕셔너리.
        """
        self.check_validate(model_configs)

        self._model_configs = model_configs

    def check_validate(self, model_configs: Dict[str, any]):
        """
        config.json의 Model 정보가 올바른지 검증합니다.
        
        Raises:
            ValueError: 필수 정보가 누락되었을 때 발생합니다.
            필수 정보는 매뉴얼을 참고해주세요.
        """
        required_keys = ["warmup", "computing_ratio", "transfer_ratio"]

        for _, model_config in model_configs.items():
            for key in required_keys:
                if key not in model_config:
                    raise ValueError(f"'{key}'가 누락되었습니다.")
        
            # warmup이 True인 경우 warmup_input이 반드시 있어야 함
            if key == "warmup" and model_config[key] == "True" and "warmup_input" not in model_config:
                raise ValueError(f"'warmup_input'가 누락되었습니다.")
            
            # computing_ratio의 값이 0보다 크거나 같아야 함
            if model_config["computing_ratio"] < 0:
                raise ValueError(f"'computing_ratio'의 값이 0보다 작습니다.")

    def get_model_names(self):
        return list(self._model_configs.keys())
        
    def get_warmup(self, model_name: str):
        return self._model_configs[model_name]["warmup"]
    
    def get_warmup_input(self, model_name: str):
        return self._model_configs[model_name]["warmup_input"]
    
    def get_computing_ratio(self, model_name: str):
        return self._model_configs[model_name]["computing_ratio"]
    
    def get_transfer_ratio(self, model_name: str):
        return self._model_configs[model_name]["transfer_ratio"]