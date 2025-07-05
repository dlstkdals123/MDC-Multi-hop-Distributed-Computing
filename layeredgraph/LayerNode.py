class LayerNode:
    def __init__(self, ip: str, layer: int, model_names: list[str] = []):
        self._ip = ip
        self._layer = layer
        self._model_names = model_names

    def get_ip(self):
        return self._ip
    
    def get_layer(self):
        return self._layer
    
    def get_model_names(self):
        return self._model_names
    
    def is_same_layer(self, target_layer_node) -> bool:
        if self._layer == target_layer_node.get_layer():
            return True
        else:
            return False
        
    def is_same_node(self, target_layer_node)  -> bool:
        if self._ip == target_layer_node.get_ip():
            return True
        else:
            return False
        
    def is_same_layer_node(self, target_layer_node) -> bool:
        if self.is_same_layer(target_layer_node) and self.is_same_node(target_layer_node):
            return True
        else:
            return False
        
    def to_string(self) -> str:
        return f"{self._ip}-{self._layer}"
    
    def __hash__(self):
        return hash(self.to_string())
    
    def __str__(self):
        return self.to_string()
    
    def __repr__(self):
        return self.to_string()

    def __eq__(self, other):
        return self.to_string() == other.to_string()

    def __ne__(self, other):
        return not(self == other)
    
    def __lt__(self, other):
        return self.get_ip() < other.get_ip()
    