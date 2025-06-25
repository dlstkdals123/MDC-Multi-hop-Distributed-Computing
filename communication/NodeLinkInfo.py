from typing import Dict
from layeredgraph import LayerNodePair

# info class for response sync
class NodeLinkInfo:
    def __init__(self, ip: str, links: Dict, computing_capacity: float, transfer_capacity: float):
        self._ip = ip
        self._links = links

        self._computing_capacity = computing_capacity
        self._transfer_capacity = transfer_capacity

    def get_ip(self):
        return self._ip

    def get_links(self):
        return self._links
    
    def get_computing_capacity(self):
        return self._computing_capacity
    
    def get_transfer_capacity(self):
        return self._transfer_capacity