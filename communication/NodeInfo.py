# info class for response NetworkInfo
class NodeInfo:
    def __init__(self, ip: str):
        self._ip = ip

    def get_ip(self):
        return self._ip