from typing import List, Dict, Union

import torch
import sys

from config.ModelConfig import ModelConfig
from utils.utils import load_model
from calflops import calculate_flops

class DNNModels:
    """
    모델 정보를 관리하는 클래스입니다.

    Attributes:
        _models (Dict[str, torch.nn.Module]): 모델 이름과 실제 모델.
        _computing (Dict[str, float]): 모델 이름과 계산량 (GFLOPs).
        _transfer (Dict[str, float]): 모델 이름과 전송량 (KB).
    """
    def __init__(self, model_names: List[str], model_config: ModelConfig, device: str):
        """
        Args:
            model_names (List[str]): 모델 이름들.
            model_config (ModelConfig): 모델 설정 정보.
            device (str): 모델을 실행하는 노드의 디바이스(cpu, cuda).
        """
        self._models: Dict[str, torch.nn.Module] = {}
        self._computing: Dict[str, float] = {}
        self._transfer: Dict[str, float] = {}

        self._init_models(model_names, model_config, device)

    def _init_models(self, model_names: List[str], model_config: ModelConfig, device: str):
        for model_name in model_names:
            model = load_model(model_name).to(device)
            self._models[model_name] = model
        
        self._init_computing_and_transfer(model_config)

    def _init_computing_and_transfer(self, model_config: ModelConfig):
        for model_name, model in self._models.items():
            input_size = model_config.get_input_size(model_name)

            with torch.no_grad():
                FLOPs, _, _ = calculate_flops(model=model, 
                                            input_shape=input_size,
                                            output_as_string=False,
                                            output_precision=4,
                                            print_results=False)

                self._computing[model_name] = FLOPs * 1e-9 # GFLOPs

                x: torch.Tensor = torch.zeros(input_size).to(self._device)

                x: Union[torch.Tensor, List[torch.Tensor]] = model(x)

                if isinstance(x, list):
                    self._transfer[model_name] = sum(x_prime.numel() * x_prime.element_size() for x_prime in x) / 1024 # KB
                else:
                    self._transfer[model_name] = x.numel() * x.element_size() / 1024 # KB

    def get_model(self, model_name: str) -> torch.nn.Module:
        return self._models[model_name]

    def get_computing(self, model_name: str) -> float:
        return self._computing[model_name]

    def get_transfer(self, model_name: str) -> float:
        return self._transfer[model_name]