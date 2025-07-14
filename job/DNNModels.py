from typing import List, Dict

import torch
import sys

from config.ModelConfig import ModelConfig
from utils.utils import load_model
from calflops import calculate_flops

class DNNModels:
    def __init__(self, model_names: List[str], model_config: ModelConfig, device: str, address: str):
        self._models: Dict[str, torch.nn.Module] = {}
        self._computing: Dict[str, float] = {}
        self._transfer: Dict[str, float] = {}

        self._device = device
        self._address = address

        self.init_models(model_names, model_config)

    def init_models(self, model_names: List[str], model_config: ModelConfig):
        for model_name in model_names:
            model = load_model(model_name).to(self._device)
            self._models[model_name] = model
            
            self.init_computing_and_transfer(model, model_config.get_input_size(model_name))
            self.warmup(model, model_config.get_input_size(model_name))

    def init_computing_and_transfer(self, model: torch.nn.Module, input_shape: List[int]):
        with torch.no_grad():
            FLOPs, _, _ = calculate_flops(model=model, 
                                        input_shape=input_shape,
                                        output_as_string=False,
                                        output_precision=4)

            self._computing[model_name] = FLOPs

            x: torch.Tensor = torch.zeros(input_shape).to(self._device)
            x: torch.Tensor = model(x)

            self._transfer[model_name] = sys.getsizeof(x.storage())
            
    def warmup(self, model: torch.nn.Module, input_shape: List[int]):
        with torch.no_grad():
            x = torch.zeros(input_shape).to(self._device)
            x : torch.Tensor = model(x)

    def get_model(self, model_name: str):
        return self._models[model_name]

    def get_computing(self, model_name: str):
        return self._computing[model_name]

    def get_transfer(self, model_name: str):
        return self._transfer[model_name]