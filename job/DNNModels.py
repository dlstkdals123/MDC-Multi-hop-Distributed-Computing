from typing import List, Dict

import torch

from config.ModelConfig import ModelConfig
from utils.utils import load_model

class DNNModels:
    def __init__(self, model_names: List[str], model_config: ModelConfig, device: str, address: str):
        self.models: Dict[str, torch.nn.Module] = {}
        self.computing_ratio: Dict[str, float] = {}
        self.transfer_ratio: Dict[str, float] = {}

        self.device = device
        self.address = address

        self.init_models(model_names, model_config)

    def init_models(self, model_names: List[str], model_config: ModelConfig):
        for model_name in model_names:
            model, _ = load_model(model_name)
            self.models[model_name] = model
            self.computing_ratio[model_name] = model_config.get_computing_ratio(model_name)
            self.transfer_ratio[model_name] = model_config.get_transfer_ratio(model_name)

            if model_config.get_warmup(model_name):
                self.warmup(model_name, model_config.get_warmup_input(model_name))
            
    def warmup(self, model_name: str, warmup_input: any):
        with torch.no_grad():
            x = torch.zeros(warmup_input).to(self.device)

            x : torch.Tensor = self.models[model_name](x)

    def get_model(self, model_name: str):
        return self.models[model_name]

    def get_computing_ratio(self, model_name: str):
        return self.computing_ratio[model_name]
    
    def get_transfer_ratio(self, model_name: str):
        return self.transfer_ratio[model_name]