class JobInfo:
    """
    작업 정보를 저장하는 클래스입니다.

    Attributes:
        _job_name (str): 작업 이름.
        _job_type (str): 작업 타입.
        _input_bytes (float): 입력 크기. 일반적으로 source의 이미지 크기 (KB).
        _source_ip (str): 작업 소스 IP.
        _terminal_destination (str): 작업 종착지 IP.
        _start_time (int): 작업 시작 시간 (ns). 동일한 작업에 대한 식별자.
    """
    def __init__(self, job_name: str, job_type: str, input_bytes: float, source_ip: str, terminal_destination: str,  start_time: int):
        self._job_name = job_name
        self._job_type = job_type
        self._input_bytes = input_bytes
        self._source_ip = source_ip
        self._terminal_destination = terminal_destination
        self._start_time = start_time

        self._delimeter = "_"

    @property
    def input_bytes(self) -> float:
        return self._input_bytes
    
    @property
    def source_ip(self) -> str:
        return self._source_ip
    
    @property
    def job_id(self) -> str:
        return self._delimeter.join([self._job_name, str(self._start_time)])
    
    @property
    def terminal_destination(self) -> str:
        return self._terminal_destination
    
    @property
    def job_type(self) -> str:
        return self._job_type
    
    @property
    def job_name(self) -> str:
        return self._job_name

    @property
    def start_time(self) -> int:
        return self._start_time

    def __str__(self):
        return self.job_id
    
    def __repr__(self):
        return self.job_id