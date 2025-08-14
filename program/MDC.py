import sys, os, json
 
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from program import Program, MDC_CONFIG_PATH
from job import JobManager, SubtaskInfo, DNNOutput, PerformanceManager
from communication import RequestConfig, NodeLinkInfo
from utils.utils import get_ip_address, get_network_capacity
from config import NetworkConfig, ModelConfig, MDCConfig

import paho.mqtt.publish as publish
import MQTTclient
import pickle
import time
from typing import Dict, Any

NANO_SECOND = 1_000_000_000
NANO_PER_MILLI_SECOND = 1_000_000

KB_PER_BYTE = 1024

class MDC(Program):
    def __init__(self, sub_configs, pub_configs):
        self.sub_configs = sub_configs
        self.pub_configs = pub_configs
        self._address = get_ip_address(["eth0", "wlan0"])
        self._node_info = RequestConfig(self._address)
        self._controller_publisher = MQTTclient.Publisher(config={
            "ip" : "192.168.1.2",
            "port" : 1883
        })
        self._node_publisher = {}

        self.topic_dispatcher = {
            "job/dnn": self.handle_dnn,
            "job/subtask_info": self.handle_subtask_info,
            "mdc/config" : self.handle_config,
            "mdc/node_info": self.handle_request_backlog,
            "mdc/finish": self.handle_finish,
        }

        self.topic_dispatcher_checker = {
            "job/dnn": [(self.check_network_config_exists, True)],
            "job/subtask_info": [(self.check_job_manager_exists, True)],
            "mdc/config": [(self.check_job_manager_exists, False)],
            "mdc/node_info": [(self.check_job_manager_exists, True)],
        }

        self._network_config = None
        self._model_config = None
        self._mdc_config = None
        self._job_manager = None
        self._neighbors = None
        self._backlogs_zero_flag = False

        self._performance_manager = PerformanceManager()
        self._computing_capacity = 0
        self._transfer_capacity = 0

        super().__init__(self.sub_configs, self.pub_configs, self.topic_dispatcher, self.topic_dispatcher_checker)

        self.init_config()
        self.request_config()

    def init_config(self):
        try:
            with open(MDC_CONFIG_PATH, 'r', encoding='utf-8') as file:  # UTF-8 인코딩 명시
                config = json.load(file)
                self._mdc_config = MDCConfig(config)
        except FileNotFoundError:
            # 파일이 없으면 디폴트 설정으로 생성
            default_config = {
                "computing_capacity": 0,
                "interface_name": "eth0",
                "wireless": False
            }
            self._mdc_config = MDCConfig(default_config)
            
            # 디폴트 설정을 파일로 저장 (UTF-8 인코딩으로)
            with open(MDC_CONFIG_PATH, 'w', encoding='utf-8') as file:
                json.dump(default_config, file, indent=2, ensure_ascii=False)


        get_network_capacity(self._mdc_config.interface_name, self._mdc_config.wireless)

    # request network information to network controller
    # sending node info.
    def request_config(self):
        while self._network_config == None:
            print("Requested config..")
            node_info_bytes = pickle.dumps(self._node_info)

            # send config byte to source ip (response)
            self._controller_publisher.publish("mdc/config", node_info_bytes)

            time.sleep(2)

    def handle_subtask_info(self, topic, data, publisher):
        subtask_info: SubtaskInfo = pickle.loads(data)

        self._job_manager.add_subtask(subtask_info)

        if self._job_manager.is_dnn_output_exists(subtask_info):
            dnn_output = self._job_manager.pop_dnn_output(subtask_info) # make another method
            self.run_dnn(dnn_output)
    
    def handle_config(self, topic, data, publisher):
        config: Dict[str, Any] = pickle.loads(data)
        self._network_config: NetworkConfig = config["network"]
        self._model_config: ModelConfig = config["model"]

        self._job_manager = JobManager(self._network_config, self._model_config)

        self._init_node_publisher()
        self._init_capacity()

        print(f"Succesfully get config.")

    def _init_node_publisher(self):
        neighbors = self._network_config.get_network_neighbors(self._address)

        for neighbor in neighbors:
            publisher = MQTTclient.Publisher(config={
                "ip" : neighbor,
                "port" : 1883
            })
            self._node_publisher[neighbor] = publisher

    def _init_capacity(self):
        self._computing_capacity = self._mdc_config.computing_capacity
        self._transfer_capacity = get_network_capacity(self._mdc_config.interface_name, self._mdc_config.wireless)

    def handle_request_backlog(self, topic, data, publisher):
        # transfer capacity check current capacity every sync time.
        computing_capacity = self._computing_capacity
        transfer_capacity = self._transfer_capacity

        self._job_manager.update_backlog(computing_capacity, transfer_capacity)
        links = self._job_manager.get_backlogs()

        performance = self._performance_manager.performance

        node_link_info = NodeLinkInfo(
            ip = self._address, 
            links = links, 
            performance = performance
        )
        
        node_link_info_bytes = pickle.dumps(node_link_info)

        # send NodeLinkInfo byte to source ip (response)
        self._controller_publisher.publish("mdc/node_info", node_link_info_bytes)

        self._performance_manager.update_performance()

    def check_network_config_exists(self, data = None) -> bool:
        return self._network_config is not None
    
    def check_model_config_exists(self, data = None) -> bool:
        return self._model_config is not None
        
    def check_job_manager_exists(self, data = None) -> bool:
        return self._job_manager is not None

    def handle_dnn(self, topic, data, publisher):
        size = len(data) / KB_PER_BYTE
        previous_dnn_output: DNNOutput = pickle.loads(data)
        previous_dnn_output.size = size
        self._performance_manager.add_input(size)
        self.run_dnn(previous_dnn_output)

    def handle_finish(self, topic, data, publisher):
        print("finish!! exit program.")
        time.sleep(5)
        os._exit(1)

    def run_dnn(self, dnn_output: DNNOutput):
        while True:
            subtask_info = dnn_output.subtask_info

            # terminal node
            if subtask_info.is_terminated():
                subtask_info_bytes = pickle.dumps(subtask_info)

                # send subtask info to controller
                self._performance_manager.add_output(dnn_output.size)
                self._controller_publisher.publish("job/response", subtask_info_bytes)

                return

            # subtask가 도착하기 전에 dnn_output이 온 경우
            if not self._job_manager.is_subtask_exists(dnn_output):
                self._job_manager.add_dnn_output(dnn_output)
                return
            
            self._job_manager.update_dnn_output(dnn_output)
            dnn_output, computing_performance = self._job_manager.run(dnn_output=dnn_output)

            subtask_info = dnn_output.subtask_info

            if subtask_info.is_transmission():
                # 다음 노드로 전송
                destination = subtask_info.destination
                destination_ip = destination.ip
                subtask_info.set_next_source()
                dnn_output_bytes = pickle.dumps(dnn_output)
                self._performance_manager.add_output(dnn_output.size)
                publish.single(f"job/{subtask_info.job_type}", dnn_output_bytes, hostname=destination_ip)

                return
            else:
                # 계산 성능 업데이트 
                self._performance_manager.update_computing(computing_performance)
                subtask_info.set_next_source()

       
if __name__ == '__main__':
    sub_configs = {
            "ip": "127.0.0.1", 
            "port": 1883,
            "topics": [
                ("job/dnn", 1),
                ("job/subtask_info", 1),
                ("mdc/config", 1),
                ("mdc/node_info", 1),
                ("mdc/finish", 1),
            ],
        }
    
    pub_configs = [
    ]
    
    mdc = MDC(sub_configs=sub_configs, pub_configs=pub_configs)
    mdc.start()