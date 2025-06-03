from typing import Dict

class NetworkInfo:
    """
    네트워크 정보를 저장하는 클래스입니다.

    Attributes:
        _experiment_name (str): 실험 이름, 결과 폴더 이름에 사용됩니다.
        _queue_name (str): 큐 이름.
        _jobs (Dict[str, any]): 작업 정보.
        _network (Dict[str, any]): 네트워크 정보.
        _router (Dict[str, any]): 라우터 정보.
        _scheduling_algorithm (str): 스케줄링 알고리즘 이름.
        _sync_time (float): 동기화 시간.
        _collect_garbage_job_time (float): 가비지 컬렉션 작업 시간.
    """
    def __init__(self, network_config: Dict[str, any]):
        """
        Args:
            network_config (Dict[str, any]): 네트워크 설정 정보가 담긴 Json 형식의 딕셔너리.
        """
        self.check_validate(network_config)

        self._network_config = network_config

        self._experiment_name = self._network_config["experiment_name"]
        self._queue_name = self._network_config["queue_name"]
        self._jobs = self._network_config["jobs"]
        self._network = self._network_config["network"]
        self._router = self._network_config["router"]
        self._scheduling_algorithm: str = self._network_config["scheduling_algorithm"]
        self._sync_time: float = self._network_config["sync_time"]
        self._collect_garbage_job_time: float = self._network_config["collect_garbage_job_time"]

    def check_validate(self, network_config: Dict[str, any]):
        """
        config.json의 Controller 정보가 올바른지 검증합니다.
        
        Raises:
            ValueError: 필수 정보가 누락되었을 때 발생합니다.
            필수 정보는 매뉴얼을 참고해주세요.
        """

        required_keys = [
            "experiment_name", 
            "queue_name", 
            "jobs", 
            "network", 
            "router", 
            "scheduling_algorithm", 
            "sync_time", 
            "collect_garbage_job_time"
        ]

        for key in required_keys:
            if key not in network_config:
                raise ValueError(f"Missing required key: {key}")


    def get_experiment_name(self):
        return self._experiment_name
    
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
    
    def get_sync_time(self):
        return self._sync_time
    
    def get_collect_garbage_job_time(self):
        return self._collect_garbage_job_time