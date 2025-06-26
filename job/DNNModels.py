from typing import Dict, List

from utils import load_model
from config import NetworkConfig, ModelConfig

import torch
from calflops import calculate_flops
import sys

class DNNModels:
    def __init__(self, network_config: NetworkConfig, device, address, model_configs: Dict[str, ModelConfig] = None):
        self._network_config = network_config
        self._device = device
        self._address = address
        self._model_configs = model_configs or {}

        self._jobs: List[str] = []
        self._models: Dict[str, torch.nn.Module] = dict()
        self._computing_ratios: Dict[str, float] = dict()
        self._transfer_ratios : Dict[str, float] = dict()

        # 단순화: 전체 모델의 computing/transfer 비율
        self._yolo_computing_ratio = 10.7  # 전체 YOLO 모델의 computing 비율
        self._yolo_transfer_ratio = 4.29   # 전체 YOLO 모델의 transfer 비율

        self.init_model()
    
    def init_model(self):
        # 현재 노드가 소지할 수 있는 모델들을 가져옴
        node_models = self._network_config.get_models().get(self._address, [])
        
        for model_name in node_models:
            self.add_model(model_name)
            self.add_computing_and_transfer(model_name)

    def add_model(self, model_name: str):
        # load whole dnn model (split 없이)
        model, _ = load_model(model_name)
        model = model.to(self._device)
        
        self._models[model_name] = model
        
    def add_computing_and_transfer(self, model_name: str):
        if "yolo" in model_name:
            # 단순화: 전체 모델의 비율 사용
            self._computing_ratios[model_name] = self._yolo_computing_ratio
            self._transfer_ratios[model_name] = self._yolo_transfer_ratio

            if not self._address in self._network_config.get_router():
                # warmup_input을 ModelConfig에서 가져옴
                model_config = self._model_configs.get(model_name)
                if model_config and model_config.get_warmup() == "True":
                    with torch.no_grad():
                        x = torch.zeros(model_config.get_warmup_input()).to(self._device)
                        _ = self._models[model_name](x)

                print(f"Succesfully load {model_name}")
            return

        # 다른 모델들의 경우
        model = self._models[model_name]
        
        # warmup_input을 ModelConfig에서 가져옴
        model_config = self._model_configs.get(model_name)
        if model_config:
            with torch.no_grad():
                x = torch.zeros(model_config.get_warmup_input()).to(self._device)
                flops, _, _ = calculate_flops(model=model, input_shape=tuple(x.shape), output_as_string=False, output_precision=4, print_results=False)
                output = model(x)
                transfer_size = sys.getsizeof(output.storage())

            # normalize with input size
            input_size = sys.getsizeof(x.storage())
            self._computing_ratios[model_name] = flops / input_size
            self._transfer_ratios[model_name] = transfer_size / input_size

        print(f"Succesfully load {model_name}")

    def get_model(self, model_name: str):
        assert model_name in self._models, f"{model_name} is not exists."
        return self._models[model_name]
    
    def get_computing(self, model_name: str, index: int = 0):
        assert model_name in self._computing_ratios, f"{model_name} is not exists."
        return self._computing_ratios[model_name]

    def get_transfer(self, model_name: str, index: int = 0):
        assert model_name in self._transfer_ratios, f"{model_name} is not exists."
        return self._transfer_ratios[model_name]
