import sys, os

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import pickle
import time
from threading import Thread
import paho.mqtt.publish as publish
import numpy as np
import posix_ipc
import mmap
import torch
try:
    from time import time_ns
except ImportError:
    from datetime import datetime
    # For compatibility with Python 3.6
    def time_ns():
        now = datetime.now()
        return int(now.timestamp() * 1e9)

from utils.utils import get_ip_address
from program import MDC
from job import JobInfo, SubtaskInfo, DNNOutput

TARGET_WIDTH = 320
TARGET_HEIGHT = 320
TARGET_DEPTH = 3


class CameraSender(MDC):
    def __init__(self, sub_config, pub_configs, job_name):
        self._address = get_ip_address(["eth0", "wlan0"])
        self._frame = None
        self._shape = (TARGET_HEIGHT, TARGET_WIDTH, TARGET_DEPTH)
        self._shared_memory_name = "jetson"
        self._memory = posix_ipc.SharedMemory(self._shared_memory_name, flags=posix_ipc.O_CREAT, mode=0o777, size=int(np.prod(self._shape) * np.dtype(np.uint8).itemsize))
        self._map_file = mmap.mmap(self._memory.fd, self._memory.size)
        # posix_ipc.close_fd(self._memory.fd)

        self._job_name = job_name
        self._job_info = None
        self._frame_list = dict()
        self._arrival_rate = 0

        super().__init__(sub_config, pub_configs)

        self.topic_dispatcher["mdc/arrival_rate"] = self.handle_arrival_rate

    def init_job_info(self):
        job_name = self._job_name
        job_type = self._network_config.get_job_type(job_name)
        input_size = None # 나중에 send_frame에서 재설정
        source_ip = self._address
        terminal_destination = self._network_config.get_job_destination(job_name)
        start_time = time_ns()

        job_info = JobInfo(job_name, job_type, input_size, source_ip, terminal_destination, start_time)

        self._job_info = job_info

    def handle_subtask_info(self, topic, data, publisher): # overriding
        subtask_info: SubtaskInfo = pickle.loads(data)

        self._job_manager.add_subtask(subtask_info)

        subtask_layer_node = subtask_info.source

        if subtask_layer_node.get_ip() == self._address and subtask_layer_node.get_layer() == 0:
            job_id = subtask_info.job_id
            input_frame = DNNOutput(torch.tensor(self._frame_list[job_id]).float().view(1, TARGET_DEPTH, TARGET_HEIGHT, TARGET_WIDTH), subtask_info)
            dnn_output, computing_capacity = self._job_manager.run(input_frame)
            destination_ip = subtask_info.destination.get_ip()

            dnn_output.subtask_info.set_next_subtask_id()

            dnn_output_bytes = pickle.dumps(dnn_output)
                
            # send job to next node
            publish.single(f"job/{subtask_info.job_type}", dnn_output_bytes, hostname=destination_ip)

            self._capacity_manager.update_computing_capacity(computing_capacity)

    def handle_arrival_rate(self, topic, data, publisher):
        arrival_rate = pickle.loads(data)

        self._arrival_rate = arrival_rate
       
    def stream_player(self):
        c = np.ndarray(self._shape, dtype=np.uint8, buffer=self._map_file)

        while True:
            self._frame = c.copy()
            time.sleep(1 / 30)

        self._map_file.close()
        self._memory.unlink()

    def start(self):
        self.wait_until_can_send()

        input("Press any key to start sending.")

        self.run_camera_streamer()
        self.run_arrival_rate_getter()

        while True:
            sleep_time = self.get_sleep_time()
            time.sleep(sleep_time)

            self.send_frame()

    def set_job_info_time(self):
        if not self._network_config:
            return False
        
        if not self._job_info:
            self.init_job_info()
            return True
        
        self._job_info.set_start_time(time_ns())
        return True
            
    def set_job_info_input_size(self, frame: np.array):
        if not self._network_config:
            return False
        
        if not self._job_info:
            self.init_job_info()
            return True
        
        input_bytes = sys.getsizeof(torch.tensor(frame).storage()) / 1024 # KB
        self._job_info.set_input_bytes(input_bytes)
        return True
            
    def wait_until_can_send(self):
        print("Waiting for network info.")
        while not (self.check_job_manager_exists() and self.check_config_exists()):
            time.sleep(1.0)
            
    def run_camera_streamer(self):
        streamer_thread = Thread(target=self.stream_player, args=())
        streamer_thread.start()

    def send_frame(self):
        current_frame = self._frame
        if self.set_job_info_time() and self.set_job_info_input_size(current_frame):
            job_info_bytes = pickle.dumps(self._job_info)
            self._frame_list[self._job_info.job_id] = current_frame

            self._controller_publisher.publish("job/request_scheduling", job_info_bytes)

    def arrival_rate_getter(self):
        node_info_bytes = pickle.dumps(self._node_info)
        while True:
            time.sleep(0.1)
            self._controller_publisher.publish("mdc/arrival_rate", node_info_bytes)

    def run_arrival_rate_getter(self):
        arrival_rate_thread = Thread(target=self.arrival_rate_getter, args=())
        arrival_rate_thread.start()

        
    def get_sleep_time(self) -> float:
        # implement any frame drop logic
        return 0.5

if __name__ == '__main__':
    sub_config = {
            "ip": "127.0.0.1", 
            "port": 1883,
            "topics": [
                ("job/dnn", 1),
                ("job/subtask_info", 1),
                ("mdc/network_info", 1),
                ("mdc/node_info", 1),
                ("mdc/arrival_rate", 1),
            ],
        }
    
    pub_configs = []

    job_name = "test job 1"

    sender = CameraSender(sub_config, pub_configs, job_name)
    sender.start()
