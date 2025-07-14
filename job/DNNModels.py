from typing import List, Dict, Union

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

        self.init_computing_and_transfer(model_config)

    def init_computing_and_transfer(self, model_config: ModelConfig):
        for model_name, model in self._models.items():
            input_shape = model_config.get_input_size(model_name)

            with torch.no_grad():
                FLOPs, _, _ = calculate_flops(model=model, 
                                            input_shape=input_shape,
                                            output_as_string=False,
                                            output_precision=4,
                                            print_result=False)

                self._computing[model_name] = FLOPs

                x: torch.Tensor = torch.zeros(input_shape).to(self._device)
                x: Union[torch.Tensor, List[torch.Tensor]] = model(x)

                if isinstance(x, list):
                    self._transfer[model_name] = sum(sys.getsizeof(x_prime.storage()) for x_prime in x)
                else:
                    self._transfer[model_name] = sys.getsizeof(x.storage())

    def get_model(self, model_name: str):
        return self._models[model_name]

    def get_computing(self, model_name: str):
        return self._computing[model_name]

    def get_transfer(self, model_name: str):
        return self._transfer[model_name]