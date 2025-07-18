import sys, os
 
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from program import Program
from communication import *
from config import ControllerConfig, NetworkConfig, ModelConfig
from layeredgraph import LayeredGraph, LayerNode
from job import JobInfo, SubtaskInfo
from utils import save_latency, save_virtual_backlog, save_path, get_ip_address

import time
import pickle, json
import paho.mqtt.publish as publish
import threading

from datetime import datetime
from typing import Dict

MS_PER_SECOND = 1_000

class Controller(Program):
    def __init__(self, sub_configs, pub_configs):
        self.sub_configs = sub_configs
        self.pub_configs = pub_configs
        self._address = get_ip_address(["eth0", "wlan0"])

        self.topic_dispatcher = {
            "mdc/config": self.handle_config,
            "mdc/node_info": self.handle_node_info,
            "job/request_scheduling": self.handle_request_scheduling,
            "job/response": self.handle_response,
            "mdc/arrival_rate": self.handle_request_arrival_rate,
            "mdc/finish": self.handle_finish,
            "mdc/network_performance_info": self.handle_network_performance_info,
        }

        self.topic_dispatcher_checker = {}

        super().__init__(self.sub_configs, self.pub_configs, self.topic_dispatcher)

        self._latency_log_path = None
        self._backlog_log_path = None
        self._path_log_path = None
        self._network_config: NetworkConfig = None
        self._controller_config: ControllerConfig = None
        self._model_config: ModelConfig = None
        self._layered_graph = None
        self._arrival_rate = 0
        self._real_arrival_rate = 0
        self._send_num = 0
        
        # job_id: start_time (ms)
        self._job_list: Dict[str, int] = {}
        self._job_list_mutex = threading.Lock()

        self._is_first_scheduling = True

        self._last_job_id = None

        self._job_info_dummy = None

        self.init_network_config()
        self.init_controller_config()
        self.init_model_config()
        self.init_path()
        self.init_layered_graph()

    def init_network_config(self):
        with open(path, 'r') as file:
            self._network_config = NetworkConfig(json.load(file)["Network"])

    def init_controller_config(self):
        with open(path, 'r') as file:
            self._controller_config = ControllerConfig(json.load(file)["Controller"])

    def init_model_config(self):
        with open(path, 'r') as file:
            model_configs = json.load(file)["Model"]
            self._model_config = ModelConfig(model_configs)

    def init_path(self):
        folder_name = self._controller_config.experiment_name + "_" + datetime.now().strftime('%m-%d_%H%M%S')
        self._latency_log_path = f"./results/{folder_name}/latency"
        os.makedirs(self._latency_log_path, exist_ok=True)

        self._backlog_log_path = f"./results/{folder_name}/backlog"
        os.makedirs(self._backlog_log_path, exist_ok=True)

        self._path_log_path = f"./results/{folder_name}/path"
        os.makedirs(self._path_log_path, exist_ok=True)
        
    def init_layered_graph(self):
        self._layered_graph = LayeredGraph(self._network_config, self._model_config)

    def init_garbage_job_collector(self):
        callback_thread = threading.Thread(target=self.garbage_job_collector, args=())
        callback_thread.start()

    def garbage_job_collector(self):
        collect_garbage_job_time = self._network_config.collect_garbage_job_time # sec
        for job_name in self._network_config.get_job_names():
            while True:
                time.sleep(collect_garbage_job_time) # sec
                
                cur_time = time.time() * MS_PER_SECOND # ms
                
                self._job_list_mutex.acquire()
                try:
                    keys_to_delete = [job_id for job_id, start_time in self._job_list.items() 
                                    if cur_time - start_time >= collect_garbage_job_time * MS_PER_SECOND] # ms
                    for k in keys_to_delete:
                        latency = collect_garbage_job_time * MS_PER_SECOND # ms
                        latency_log_file_path = f"{self._latency_log_path}/{job_name}.csv"
                        save_latency(latency_log_file_path, latency)
                        del self._job_list[k]
                    
                    print(f"Deleted {len(keys_to_delete)} jobs. {len(self._job_list)} remains.")
                finally:
                    self._job_list_mutex.release()

    def init_record_virtual_backlog(self):
        record_virtual_backlog_thread = threading.Thread(target=self.record_virtual_backlog, args=())
        record_virtual_backlog_thread.start()

    def record_virtual_backlog(self):
        backlog_log_file_path = f"{self._backlog_log_path}/total_backlog.csv"
        while True:
            time.sleep(0.1)
            self._layered_graph.update_graph()
            save_virtual_backlog(backlog_log_file_path, self._layered_graph.get_layered_graph_backlog())

    def init_sync_backlog(self):
        sync_backlog_thread = threading.Thread(target=self.sync_backlog, args=())
        sync_backlog_thread.start()

    def sync_backlog(self):
        while True:
            time.sleep(self._controller_config.sync_time)
            for node_ip in self._network_config.get_network_list():
                # send RequestBacklog byte to source ip (response)
                request_backlog = RequestBacklog()
                request_backlog_bytes = pickle.dumps(request_backlog)
                try:
                    publish.single("mdc/node_info", request_backlog_bytes, hostname=node_ip)
                except:
                    pass

    def init_sync_network_performance(self):
        sync_network_performance_thread = threading.Thread(target=self.sync_network_performance, args=())
        sync_network_performance_thread.start()

    def sync_network_performance(self):
        while True:
            time.sleep(self._controller_config.sync_time)
            for node_ip in self._network_config.get_network_list():
                # send RequestBacklog byte to source ip (response)
                request_network_performance = RequestNetworkPerformance()
                request_network_performance_bytes = pickle.dumps(request_network_performance)
                try:
                    publish.single("mdc/network_performance_info", request_network_performance_bytes, hostname=node_ip)
                except:
                    pass

    def init_measure_arrival_rate(self):
        measure_arrival_rate_thread = threading.Thread(target=self.measure_arrival_rate, args=())
        measure_arrival_rate_thread.start()

    def measure_arrival_rate(self):
        while True:
            time.sleep(1)
            self._real_arrival_rate = self._send_num / 30
            self._layered_graph.update_expected_arrival_rate(self._real_arrival_rate)
            self._send_num = 0

    def handle_config(self, topic, payload, publisher):
        # get source ip address
        node_info: RequestConfig = pickle.loads(payload)
        ip = node_info.ip

        print(f"ip: {ip} requested config.")

        config = {
            "network": self._network_config,
            "model": self._model_config
        }

        config_bytes = pickle.dumps(config)

        # send config byte to source ip (response)
        publish.single("mdc/config", config_bytes, hostname=ip)

        print(f"Succesfully respond to ip: {ip}.")

    def handle_node_info(self, topic, payload, publisher):
        node_link_info: NodeLinkInfo = pickle.loads(payload)
        node_ip = node_link_info.ip
        links = node_link_info.links
        
        total_links = self._layered_graph.get_links(node_ip)
        for link in total_links:
            links.setdefault(link, 0)
            
        self._layered_graph.set_graph(links)
        self._layered_graph.set_capacity(
            node_ip,
            node_link_info.computing_capacity,
            node_link_info.transfer_capacity
        )

        if self._job_info_dummy:
            path = self._layered_graph.schedule(
                self._job_info_dummy.source_ip, 
                self._job_info_dummy
            )
            self._arrival_rate = self._layered_graph.get_arrival_rate(path)

    def handle_request_scheduling(self, topic, payload, publisher):
        self._send_num += 1 # for measure real arrival rate
        job_info: JobInfo = pickle.loads(payload)

        if self._is_first_scheduling:
            self.init_record_virtual_backlog()
            self._is_first_scheduling = False
            self._job_info_dummy = job_info

        # register start time
        self._job_list[job_info.job_id] = time.time() * MS_PER_SECOND # ms

        path = self._layered_graph.schedule(job_info)
        self._arrival_rate = self._layered_graph.get_arrival_rate(path)
        self._layered_graph.update_path_backlog(job_info=job_info, path=path)
        path_log_file_path = f"{self._path_log_path}/path.csv"
        save_path(path_log_file_path, path)
        
        for i in range(len(path)):
            source = path[i][0]
            destination = path[i][1]
            model_name = path[i][2]
            subtask_info = SubtaskInfo(job_info, source, destination, model_name, i, len(path))
            subtask_info_bytes = pickle.dumps(subtask_info)
            # send SubtaskInfo byte to source ip
            publish.single("job/subtask_info", subtask_info_bytes, hostname=source.get_ip())
            
    def handle_response(self, topic, payload, publisher):
        subtask_info: SubtaskInfo = pickle.loads(payload)
        job_id = subtask_info.job_id
        self._job_list_mutex.acquire()
        start_time = self._job_list[job_id]
        del self._job_list[job_id]
        self._job_list_mutex.release()
        finish_time = time.time() * MS_PER_SECOND # ms

        latency = finish_time - start_time
        latency_log_file_path = f"{self._latency_log_path}/{subtask_info.job_name}.csv"
        save_latency(latency_log_file_path, latency)

        if job_id == self._last_job_id:
            self.notify_finish()
            print("finish!! exit program.")
            time.sleep(5)
            os._exit(1)

    def handle_network_performance_info(self, topic, payload, publisher):
        network_performance: NetworkPerformance = pickle.loads(payload)

        if network_performance.ip == "192.168.1.5":
            self._layered_graph.update_network_performance_info('end', network_performance.gpu_capacity)

        elif network_performance.ip == "192.168.1.7":
            self._layered_graph.update_network_performance_info('edge', network_performance.gpu_capacity)

        elif network_performance.ip == "192.168.1.8":
            self._layered_graph.update_network_performance_info('cloud', network_performance.gpu_capacity)

    def notify_finish(self):
        for node_ip in self._network_config.get_network_list():
            # send finish to nodes
            try:
                publish.single("mdc/finish", b"", hostname=node_ip)
            except:
                pass

    def handle_request_arrival_rate(self, topic, payload, publisher):
        # get source ip address
        node_info: RequestConfig = pickle.loads(payload)
        ip = node_info.ip

        arrival_rate_bytes = pickle.dumps(self._arrival_rate)

        # send arrival_rate byte to source ip (response)
        publish.single("mdc/arrival_rate", arrival_rate_bytes, hostname=ip)

    def handle_finish(self, topic, payload, publisher):
        job_info: JobInfo = pickle.loads(payload)

        self._last_job_id = job_info.job_id

    def start(self):
        self.init_garbage_job_collector()
        self.init_sync_backlog()
        self.init_sync_network_performance()
        self.init_measure_arrival_rate()


if __name__ == '__main__':

    sub_configs = {
            "ip": "127.0.0.1", 
            "port": 1883,
            "topics": [
                ("mdc/config", 1),
                ("job/response", 1),
                ("mdc/node_info", 1),
                ("job/request_scheduling", 1),
                ("mdc/arrival_rate", 1),
                ("mdc/finish", 1),
                ("mdc/network_performance_info", 1),
            ],
        }
    
    global path
    path = "config/config.json"

    pub_configs = []
    
    controller = Controller(sub_configs=sub_configs, pub_configs=pub_configs)
    controller.start()