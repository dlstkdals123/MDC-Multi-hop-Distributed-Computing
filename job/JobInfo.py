import time

class JobInfo:
    def __init__(self, source_ip: str, terminal_destination: str, job_type: str, job_name: str):
        self._source_ip = source_ip
        self._terminal_destination = terminal_destination
        self._job_type = job_type
        self._job_name = job_name
        self._start_time = time.time_ns()

        self._delimeter = "_"

    def get_source_ip(self):
        return self._source_ip

    def get_job_id(self):
        return self._delimeter.join([self._job_name, self._start_time])
    
    def get_terminal_destination(self):
        return self._terminal_destination
    
    def get_job_type(self):
        return self._job_type
    
    def get_job_name(self):
        return self._job_name
    
    def set_start_time(self, start_time: float):
        self._start_time = start_time

    def __eq__(self, other):
        return self.get_job_id() == other.get_job_id()

    def __str__(self):
        return self.get_job_id()
    
    def __repr__(self):
        return self.get_job_id()