from typing import Dict, Any
import sys, os, json

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import pickle
import time
from threading import Thread
import paho.mqtt.publish as publish
import cv2
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
from program import SENDER_CONFIG_PATH
from program.MDC import MDC
from job import JobInfo, SubtaskInfo, DNNOutput, PerformanceManager, JobManager
from config import NetworkConfig, ModelConfig, SenderConfig

TARGET_WIDTH = 320
TARGET_HEIGHT = 320
TARGET_DEPTH = 3

KB_PER_BYTE = 1024


class VideoSender(MDC):
    def __init__(self, sub_configs, pub_configs, job_name):
        self._address = get_ip_address(["eth0", "wlan0"])
        self._frame = None

        self._job_name = job_name
        self._job_info = None
        self._frame_list = dict()

        self._sender_config = None

        self._performance_manager = PerformanceManager()

        self._init_sender_config()

        super().__init__(sub_configs, pub_configs)

    def _init_sender_config(self):
        try:
            with open(SENDER_CONFIG_PATH, 'r', encoding='utf-8') as file:  # UTF-8 인코딩 명시
                config = json.load(file)
                self._sender_config = SenderConfig(config)
        except FileNotFoundError:
            # 파일이 없으면 디폴트 설정으로 생성
            default_config = {
                "frame_delay": 0.3
            }
            self._sender_config = SenderConfig(default_config)
            
            # 디폴트 설정을 파일로 저장 (UTF-8 인코딩으로)
            with open(SENDER_CONFIG_PATH, 'w', encoding='utf-8') as file:
                json.dump(default_config, file, indent=2, ensure_ascii=False)

    def init_job_info(self, input_bytes: float):
        job_name = self._job_name
        job_type = self._network_config.get_job_type(job_name)
        source_ip = self._address
        terminal_destination = self._network_config.get_job_destination(job_name)
        start_time = time_ns() # 식별자를 위해서 ns 단위로 설정

        job_info = JobInfo(job_name, job_type, input_bytes, source_ip, terminal_destination, start_time)

        self._job_info = job_info

    def handle_subtask_info(self, topic, data, publisher): # overriding
        subtask_info: SubtaskInfo = pickle.loads(data)

        self._job_manager.add_subtask(subtask_info)

        subtask_layer_node = subtask_info.source

        if subtask_layer_node.ip == self._address:
            job_id = subtask_info.job_id
            input_frame = DNNOutput(torch.tensor(self._frame_list[job_id]).float().view(1, TARGET_DEPTH, TARGET_HEIGHT, TARGET_WIDTH), subtask_info)
            dnn_output, _ = self._job_manager.run(input_frame)
            destination_ip = subtask_info.destination.ip

            dnn_output.subtask_info.set_next_source()

            dnn_output_bytes = pickle.dumps(dnn_output)
                
            # send job to next node
            publish.single(f"job/{subtask_info.job_type}", dnn_output_bytes, hostname=destination_ip)

            self._performance_manager.add_output(len(dnn_output_bytes) / KB_PER_BYTE)

    def stream_player(self):
        cap = cv2.VideoCapture("video/JN.mp4")
        
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                print("Video restarted.")
                continue
                
            resize_frame = cv2.resize(frame, (320, 320), interpolation=cv2.INTER_CUBIC)
            self._frame = resize_frame
            time.sleep(1 / 30)

    def start(self):
        self.wait_until_can_send()

        input("Press any key to start sending.")

        self.run_camera_streamer()

        while True:
            time.sleep(self._sender_config.frame_delay)

            if self._frame is not None:
                self.send_frame()
            
    def wait_until_can_send(self):
        print("Waiting for config.")
        while not (self.check_job_manager_exists() and self.check_network_config_exists()):
            time.sleep(1.0)
            
    def run_camera_streamer(self):
        streamer_thread = Thread(target=self.stream_player, args=())
        streamer_thread.start()

    def send_frame(self):
        current_frame = self._frame

        input_bytes = current_frame.nbytes / KB_PER_BYTE
        self.init_job_info(input_bytes)

        job_info_bytes = pickle.dumps(self._job_info)
        self._frame_list[self._job_info.job_id] = current_frame

        self._controller_publisher.publish("job/request_scheduling", job_info_bytes)

if __name__ == '__main__':
    sub_configs = {
            "ip": "127.0.0.1", 
            "port": 1883,
            "topics": [
                ("job/dnn", 1),
                ("job/subtask_info", 1),
                ("mdc/config", 1),
                ("mdc/node_info", 1),
            ],
        }
    
    pub_configs = []

    job_name = "test job 1"

    sender = VideoSender(sub_configs, pub_configs, job_name)
    sender.start()
