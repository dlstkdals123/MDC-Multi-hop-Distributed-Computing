from typing import List, Dict

import torch

from config.ModelConfig import ModelConfig
from utils.utils import load_model

class DNNModels:
    def __init__(self, model_names: List[str], model_config: ModelConfig, device: str, address: str):
        self._models: Dict[str, torch.nn.Module] = {}
        self._computing_ratio: Dict[str, float] = {}
        self._transfer_ratio: Dict[str, float] = {}

        self._device = device
        self._address = address

        self.init_models(model_names, model_config)

    def init_models(self, model_names: List[str], model_config: ModelConfig):
        for model_name in model_names:
            model, _ = load_model(model_name)
            # 모델을 올바른 디바이스로 이동
            model = model.to(self._device)
            self._models[model_name] = model
            self._computing_ratio[model_name] = model_config.get_computing_ratio(model_name)
            self._transfer_ratio[model_name] = model_config.get_transfer_ratio(model_name)

            if model_config.get_warmup(model_name):
                self.warmup(model_name, model_config.get_warmup_input(model_name))
            
    def warmup(self, model_name: str, warmup_input: any):
        with torch.no_grad():
            x = torch.zeros(warmup_input).to(self._device)
            
            # 모델을 올바른 디바이스로 이동
            model = self._models[model_name].to(self._device)
            x : torch.Tensor = model(x)

    def get_model(self, model_name: str):
        return None if model_name == "" else self._models[model_name]

    def get_computing_ratio(self, model_name: str):
        return self._computing_ratio[model_name]
    
    def get_transfer_ratio(self, model_name: str):
        return self._transfer_ratio[model_name] if model_name != "" else 1