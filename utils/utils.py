import subprocess, socket, re, os
from typing import Dict

import csv

import torch
from torchvision.models import resnet18, mobilenet_v2
from yolov5.Yolov5 import P1, P2, P3, P4

NANO_PER_MILLISECOND = 1_000_000

def get_ip_address(interface_name=["eth0"]):
    # check os
    for interface in interface_name:

        if os.name == "nt":  # windows
            ip = get_ip_address_windows(interface)
        else:  # linux / unix
            ip = get_ip_address_linux(interface)

        if "192.168.1" in ip:
            return ip

def get_ip_address_windows(interface_name='eth0'):
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

def get_ip_address_linux(interface_name='eth0'):
    try:
        ip_addr_output = subprocess.check_output(["ip", "addr", "show", interface_name], encoding='utf-8')

        ip_pattern = re.compile(r"inet (\d+\.\d+\.\d+\.\d+)/")
        ip_match = ip_pattern.search(ip_addr_output)
        if ip_match:
            return ip_match.group(1)
        else:
            return "IP address not found"
    except subprocess.CalledProcessError:
        return "Failed to execute ip command or interface not found"
    

def save_latency(file_path: str, latency: float):
    # 파일이 존재하는지 확인
    file_exists = os.path.exists(file_path)

    latency /= NANO_PER_MILLISECOND

    # 파일에 데이터 쓰기
    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # 파일이 새로 만들어진 경우 열 이름을 씁니다.
        if not file_exists:
            writer.writerow(["latency (ms)"])
        
        # 데이터 행을 파일에 씁니다. 소수점 둘째자리까지 반올림
        writer.writerow([round(latency, 2)])

def save_virtual_backlog(file_path, virtual_backlog):
    # 파일이 존재하는지 확인
    file_exists = os.path.exists(file_path)

    sorted_virtual_backlog = sorted(virtual_backlog.items(), key=lambda item: item[0])
    links = [link.to_string() for link, _ in sorted_virtual_backlog]
    backlogs = [backlog for _, backlog in sorted_virtual_backlog]

    sum_GFLOPs = 0 # GFLOPs
    sum_KB = 0 # KB
    
    computing_count = 0
    transmission_count = 0

    for idx, (link, backlog) in enumerate(sorted_virtual_backlog):
        if link.is_same_node():
            sorted_virtual_backlog[idx] = (f"(computing) {link.source.to_string()}", backlog)
            sum_GFLOPs += backlog # GFLOPs
            computing_count += 1
        else:
            sorted_virtual_backlog[idx] = (f"(transmission) {link.to_string()}", backlog)
            sum_KB += backlog # KB
            transmission_count += 1
            
    sum_GFLOPs_avg = sum_GFLOPs / computing_count if computing_count > 0 else 0
    sum_KB_avg = sum_KB / transmission_count if transmission_count > 0 else 0

    headers = ["sum_GFLOPs", "avg_GFLOPs", "sum_KB", "avg_KB"] + links
    datas = [sum_GFLOPs, sum_GFLOPs_avg, sum_KB, sum_KB_avg] + backlogs

    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)

        if not file_exists:
            writer.writerow(headers)

        writer.writerow(datas)

def save_performance(file_path, performance):
    # 파일이 존재하는지 확인
    file_exists = os.path.exists(file_path)

    # 노드와 값을 정렬
    sorted_performance = sorted(performance.items(), key=lambda item: item[0].to_string())

    sorted_nodes = [node.to_string() for node, _ in sorted_performance]
    sorted_input_values = [value.input for _, value in sorted_performance]
    sorted_output_values = [value.output for _, value in sorted_performance]
    sorted_computing_values = [value.computing for _, value in sorted_performance]
    sorted_dropped_input_values = [value.dropped_input for _, value in sorted_performance]
    sorted_dropped_output_values = [value.dropped_output for _, value in sorted_performance]

    sum_input = sum(sorted_input_values)
    avg_input = sum_input / len(sorted_input_values) if sorted_input_values else 0
    sum_output = sum(sorted_output_values)
    avg_output = sum_output / len(sorted_output_values) if sorted_output_values else 0
    sum_computing = sum(sorted_computing_values)
    avg_computing = sum_computing / len(sorted_computing_values) if sorted_computing_values else 0
    sum_dropped_input = sum(sorted_dropped_input_values)
    avg_dropped_input = sum_dropped_input / len(sorted_dropped_input_values) if sorted_dropped_input_values else 0
    sum_dropped_output = sum(sorted_dropped_output_values)
    avg_dropped_output = sum_dropped_output / len(sorted_dropped_output_values) if sorted_dropped_output_values else 0

    headers = ["sum_input (KB/s)", "avg_input (KB/s)", "sum_output (KB/s)", "avg_output (KB/s)", "sum_computing (GFLOPs/s)", "avg_computing (GFLOPs/s)", "sum_dropped_input (packet/s)", "avg_dropped_input (packet/s)", "sum_dropped_output (packet/s)", "avg_dropped_output (packet/s)"] + \
        [f"{node}(input)" for node in sorted_nodes] + [f"{node}(output)" for node in sorted_nodes] + [f"{node}(computing)" for node in sorted_nodes] + \
        [f"{node}(dropped_input)" for node in sorted_nodes] + [f"{node}(dropped_output)" for node in sorted_nodes]
    
    datas = [sum_input, avg_input, sum_output, avg_output, sum_computing, avg_computing, sum_dropped_input, avg_dropped_input, sum_dropped_output, avg_dropped_output] + sorted_input_values + sorted_output_values + sorted_computing_values + sorted_dropped_input_values + sorted_dropped_output_values

    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(datas)

def save_node_delay(file_path, node_delay):
    # 파일이 존재하는지 확인
    file_exists = os.path.exists(file_path)

    # 노드 정렬
    sorted_nodes = sorted(node_delay.keys(), key=lambda node: node.to_string())
    node_names = [node.to_string() for node in sorted_nodes]

    # 헤더 생성 - 각 노드에서 다른 노드로의 지연시간
    headers = []
    for source in node_names:
        for dest in node_names:
            headers.append(f"{source}->{dest} (ms)")

    # 데이터 생성
    datas = []
    total_delay = 0
    delay_count = 0
    
    for source in sorted_nodes:
        for dest in sorted_nodes:
            delay = node_delay[source].node_delay.get(dest, 0)
            datas.append(delay)
            if delay > 0:
                total_delay += delay
                delay_count += 1

    avg_delay = total_delay / delay_count if delay_count > 0 else 0
    
    # 전체 합계와 평균을 앞에 추가
    headers = ["sum_delay (ms)", "avg_delay (ms)"] + headers
    datas = [total_delay, avg_delay] + datas

    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)    
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(datas)

def save_path(file_path, path):
    # 파일이 존재하는지 확인
    file_exists = os.path.exists(file_path)

    path_list = []
    for layer_node_pair, model_name in path:
        if layer_node_pair.is_same_node():
            path_list.append(f"(computing) {layer_node_pair.to_string()}: {model_name}")
        else:
            path_list.append(f"(transmission) {layer_node_pair.to_string()}")

    # 파일에 데이터 쓰기
    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # 파일이 새로 만들어진 경우 열 이름을 씁니다.
        if not file_exists:
            writer.writerow(["path"])
        
        # 각 path를 별도 컬럼으로 저장
        writer.writerow(path_list)
       
def split_model(model: torch.nn.Module, split_point, flatten_index: int) -> torch.nn.Module:
    start, end = split_point
    layers = list(model.children())
    if flatten_index != None:
        layers.insert(flatten_index, torch.nn.Flatten())
    splited_model = torch.nn.Sequential(*layers[start:end])
    return splited_model

def load_model(model_name) -> torch.nn.Module:

    available_model_list = ["yolov5", "resnet-18", "resnet-50", "mobilenet_v2"]

    assert model_name in available_model_list, f"Model must be in {available_model_list}."

    if model_name == "yolov5":
        models = torch.nn.Sequential(P1(), P2(), P3(), P4())
        return models
    
    elif model_name == "resnet-18":
        model = resnet18(pretrained=True)
        model.eval()
        return model
    
    elif model_name == "resnet-50":
        return None
    
    elif model_name == "mobilenet_v2":
        model = mobilenet_v2(pretrained=True)
        model.eval()
        return model
    
def ensure_path_exists(path, is_file=False):
    """
    지정된 경로에 폴더 또는 파일이 있는지 확인하고, 없으면 생성합니다.
    
    Parameters:
    path (str): 확인할 경로
    is_file (bool): 파일 경로인지 여부를 지정 (True로 설정 시 파일이 없을 경우 빈 파일 생성)
    """
    if is_file:
        # 파일의 상위 폴더가 없으면 폴더를 먼저 생성
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # 파일이 없으면 빈 파일 생성
        if not os.path.exists(path):
            with open(path, 'w') as f:
                pass
            print(f"File created at: {path}")
        else:
            print(f"File already exists at: {path}")
    else:
        # 폴더가 없으면 폴더 생성
        os.makedirs(path, exist_ok=True)
        print(f"Directory ensured at: {path}")