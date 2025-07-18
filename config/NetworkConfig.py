import importlib
from typing import Dict, List

class NetworkConfig:
    """
    네트워크 정보를 저장하는 클래스입니다.

    Attributes:
        _queue_name (str): 큐 이름.
        _scheduling_algorithm (str): 스케줄링 알고리즘 이름.
        _collect_garbage_job_time (int): 가비지 컬렉션 작업 시간. (sec)
        _jobs (Dict[str, any]): 작업 정보.
        _network (Dict[str, any]): 네트워크 정보.
        _router (Dict[str, any]): 라우터 정보.
        _models (Dict[str, List[str]]): 각 노드가 소지할 수 있는 모델들.
    """
    def __init__(self, network_config: Dict[str, any]):
        """
        Args:
            network_config (Dict[str, any]): 네트워크 설정 정보가 담긴 Json 형식의 딕셔너리.
        """
        self._check_validate(network_config)

        self._queue_name: str = network_config["queue_name"]
        self._scheduling_algorithm: str = network_config["scheduling_algorithm"]
        self._collect_garbage_job_time: int = int(network_config["collect_garbage_job_time"])
        self._jobs: Dict[str, any] = network_config["jobs"]
        self._network: Dict[str, any] = network_config["network"]
        self._router: List[str] = network_config["router"]
        self._models: Dict[str, any] = network_config["models"]

    def _check_validate(self, network_config: Dict[str, any]):
        """
        config.json의 Controller 정보가 올바른지 검증합니다.
        
        Raises:
            ValueError: 필수 정보가 누락되었을 때 발생합니다.
        """

        required_keys = [
            "queue_name", 
            "scheduling_algorithm",
            "collect_garbage_job_time",
            "jobs", 
            "network", 
            "router", 
            "models"
        ]

        for key in required_keys:
            if key not in network_config:
                raise ValueError(f"Missing required key: {key}")
        
        # 스케줄링 알고리즘 클래스 존재 여부 검증
        self._validate_scheduling_algorithm(network_config["scheduling_algorithm"])
        
        # jobs 검증
        self._validate_jobs(network_config["jobs"])
    
    def _validate_scheduling_algorithm(self, algorithm_path: str):
        """
        스케줄링 알고리즘 클래스가 실제로 존재하는지 검증합니다.
        
        Args:
            algorithm_path (str): 스케줄링 알고리즘 클래스 경로 (예: "scheduling/RandomSelection.py")
        
        Raises:
            ValueError: 스케줄링 알고리즘 클래스가 존재하지 않을 때 발생합니다.
        """
        try:
            # 파일 경로에서 모듈 경로로 변환
            if algorithm_path.endswith('.py'):
                module_path = algorithm_path[:-3].replace('/', '.')
            else:
                module_path = algorithm_path.replace('/', '.')
            
            # 모듈이 존재하는지 확인
            importlib.import_module(module_path)
            
        except ImportError:
            raise ValueError(f"Scheduling algorithm class not found: {algorithm_path}")
        except Exception as e:
            raise ValueError(f"Error validating scheduling algorithm {algorithm_path}: {str(e)}")

    def _validate_jobs(self, jobs: Dict[str, any]):
        """
        jobs 설정이 올바른지 검증합니다.
        
        Args:
            jobs (Dict[str, any]): jobs 설정 정보
            
        Raises:
            ValueError: jobs 설정이 올바르지 않을 때 발생합니다.
        """
        if len(jobs) == 0:
            raise ValueError("jobs cannot be empty")
        
        required_job_keys = ["job_type", "source", "destination"]
        
        # 필수 키 검증
        for _, job_info in jobs.items():
            for key in required_job_keys:
                if key not in job_info:
                    raise ValueError(f"Missing required key: {key}")

    @property
    def queue_name(self) -> str:
        return self._queue_name
    
    @property
    def scheduling_algorithm(self) -> str:
        return self._scheduling_algorithm
    
    @property
    def collect_garbage_job_time(self) -> int:
        return self._collect_garbage_job_time

    def get_job_names(self) -> List[str]:
        return list(self._jobs.keys())

    def get_job_type(self, job_name: str) -> str:
        return self._jobs[job_name]["job_type"]
    
    def get_job_source(self, job_name: str) -> str:
        return self._jobs[job_name]["source"]
    
    def get_job_destination(self, job_name: str) -> str:
        return self._jobs[job_name]["destination"]
    
    def get_network_list(self) -> List[str]:
        return list(self._network.keys())
    
    def get_network_neighbors(self, source_ip: str) -> List[str]:
        return self._network[source_ip]

    @property
    def router(self) -> List[str]:
        return self._router

    def get_models(self, ip: str) -> List[str]:
        return self._models[ip]