from typing import Dict, List

class NetworkConfig:
    """
    네트워크 정보를 저장하는 클래스입니다.

    Attributes:
        _queue_name (str): 큐 이름.
        _jobs (Dict[str, any]): 작업 정보.
        _network (Dict[str, any]): 네트워크 정보.
        _router (Dict[str, any]): 라우터 정보.
        _scheduling_algorithm (str): 스케줄링 알고리즘 이름.
        _collect_garbage_job_time (float): 가비지 컬렉션 작업 시간.
        _models (Dict[str, List[str]]): 각 노드가 소지할 수 있는 모델들.
    """
    def __init__(self, network_config: Dict[str, any]):
        """
        Args:
            network_config (Dict[str, any]): 네트워크 설정 정보가 담긴 Json 형식의 딕셔너리.
        """
        self.check_validate(network_config)

        self._queue_name = network_config["queue_name"]
        self._jobs = network_config["jobs"]
        self._network = network_config["network"]
        self._router = network_config["router"]
        self._scheduling_algorithm: str = network_config["scheduling_algorithm"]
        self._collect_garbage_job_time: float = network_config["collect_garbage_job_time"]
        
        # Models 섹션이 있으면 추가
        self._models = network_config.get("Models", {})

    def check_validate(self, network_config: Dict[str, any]):
        """
        config.json의 Controller 정보가 올바른지 검증합니다.
        
        Raises:
            ValueError: 필수 정보가 누락되었을 때 발생합니다.
            필수 정보는 매뉴얼을 참고해주세요.
        """

        required_keys = [
            "queue_name", 
            "jobs", 
            "network", 
            "router", 
            "scheduling_algorithm",
            "collect_garbage_job_time"
        ]

        for key in required_keys:
            if key not in network_config:
                raise ValueError(f"Missing required key: {key}")
    
    def get_queue_name(self):
        return self._queue_name

    def get_jobs(self):
        return self._jobs
    
    def get_network(self):
        return self._network
    
    def get_router(self):
        return self._router
    
    def get_scheduling_algorithm(self):
        return self._scheduling_algorithm
    
    def get_collect_garbage_job_time(self):
        return self._collect_garbage_job_time
    
    def get_models(self):
        """각 노드가 소지할 수 있는 모델들을 반환합니다."""
        return self._models
    
    def get_model_config(self, model_name: str):
        """특정 모델의 설정을 반환합니다. 이는 Controller에서 ModelConfig를 통해 처리됩니다."""
        # 이 메서드는 Controller에서 ModelConfig를 통해 처리되므로 None을 반환
        # 실제 구현은 Controller에서 ModelConfig를 통해 처리
        return None