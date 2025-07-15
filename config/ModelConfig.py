from typing import Dict, List, Tuple

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
        self.init_model_configs(model_configs)

        self._model_configs: Dict[str, any] = model_configs

    def check_validate(self, model_configs: Dict[str, any]):
        """
        config.json의 Model 정보가 올바른지 검증합니다.
        
        Raises:
            ValueError: 필수 정보가 누락되었을 때 발생합니다.
        """
        required_keys = ["input_size"]

        for _, model_config in model_configs.items():
            for key in required_keys:
                if key not in model_config:
                    raise ValueError(f"'{key}'가 누락되었습니다.")

    def init_model_configs(self, model_configs: Dict[str, any]):
        for model_name, model_config in model_configs.items():
            model_config["input_size"] = tuple(model_config["input_size"])

    def get_model_names(self) -> List[str]:
        return list(self._model_configs.keys())
        
    def get_input_size(self, model_name: str) -> Tuple[int, ...]:
        return self._model_configs[model_name]["input_size"]