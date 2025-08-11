import subprocess, socket, re, os
from typing import List

import csv

import torch
from torchvision.models import resnet18, mobilenet_v2
from yolov5.Yolov5 import P1, P2, P3, P4

NANO_PER_MILLISECOND = 1_000_000
GIGABYTES = 1_000_000_000

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
        if link.is_computing():
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

    # datas가 전부 0이면 return
    if all(data == 0 for data in datas):
        return

    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)

        if not file_exists:
            writer.writerow(headers)

        writer.writerow(datas)

def save_performance(file_path, performances, routers: List[str]):
    # 파일이 존재하는지 확인
    file_exists = os.path.exists(file_path)

    ip_and_performance = []
    for node, performance in performances.items():
        ip_and_performance.append((node.ip, performance))

    # 노드와 값을 정렬
    if all(perf.is_empty() for perf in performances.values()):
        return
    
    ip_and_performance.sort(key=lambda x: x[0])

    sorted_nodes = [ip for ip, _ in ip_and_performance]
    sorted_actual_queue_backlog_values = [value.actual_queue_backlog for _, value in ip_and_performance]
    sorted_computing_values = [value.computing for ip, value in ip_and_performance if ip not in routers]

    sum_actual_queue_backlog = sum(sorted_actual_queue_backlog_values)
    avg_actual_queue_backlog = sum_actual_queue_backlog / len(sorted_actual_queue_backlog_values) if sorted_actual_queue_backlog_values else 0
    sum_computing = sum(sorted_computing_values)
    avg_computing = sum_computing / len(sorted_computing_values) if sorted_computing_values else 0

    headers = ["sum_actual_queue_backlog (KB/s)", "avg_actual_queue_backlog (KB/s)", "sum_computing (GFLOPs/s)", "avg_computing (GFLOPs/s)"] + \
        [f"{ip}(actual_queue_backlog)" for ip in sorted_nodes] + [f"{ip}(computing)" for ip in sorted_nodes if ip not in routers]
    
    datas = [sum_actual_queue_backlog, avg_actual_queue_backlog, sum_computing, avg_computing] + \
        sorted_actual_queue_backlog_values + sorted_computing_values

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
        if layer_node_pair.is_computing():
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

def get_network_capacity(interface_name='eth0', wireless=False) -> float:
    """
    네트워크 인터페이스의 최대 대역폭(capacity)을 가져옵니다.
    
    Args:
        interface_name (str): 확인할 네트워크 인터페이스 이름
        wireless (bool): 무선 인터페이스 여부 (True: 무선, False: 유선)
        
    Returns:
        dict: 최대 대역폭 정보 (bps)
    """
    if os.name == "nt":  # windows
        capacity = get_network_capacity_windows(interface_name, wireless)
    else:  # linux / unix
        capacity = get_network_capacity_linux(interface_name, wireless)
    
    return capacity

def get_network_capacity_windows(interface_name, wireless):
    """
    Windows에서 네트워크 인터페이스의 최대 대역폭을 가져옵니다.
    """
    cmd = f'wmic nic where "NetConnectionID=\'{interface_name}\' AND NetEnabled=TRUE" get Speed /value'
    output = subprocess.check_output(cmd, shell=True, encoding='utf-8')
    
    # 출력에서 Speed 값 추출
    lines = output.strip().split('\n')
    for line in lines:
        if line.startswith('Speed='):
            speed_str = line.split('=', 1)[1].strip()
            if speed_str and speed_str != '':
                return float(speed_str)
    
    # Raise error if Speed information cannot be found
    raise ValueError(f"Speed information for network interface '{interface_name}' not found.")

def get_network_capacity_linux(interface_name, wireless):
    """
    Linux에서 네트워크 인터페이스의 최대 대역폭을 가져옵니다.
    """
    if wireless:
        return _get_wireless_capacity_linux(interface_name)
    else:
        return _get_wired_capacity_linux(interface_name)

def _get_wireless_capacity_linux(interface_name):
    """
    Linux에서 무선 네트워크 인터페이스의 최대 대역폭을 가져옵니다.
    """
    try:
        # 무선 인터페이스인 경우 iwconfig를 사용
        cmd = f"iwconfig {interface_name}"
        output = subprocess.check_output(cmd, shell=True, encoding='utf-8', stderr=subprocess.DEVNULL)
        
        # 무선 인터페이스에서는 Bit Rate 정보 추출
        lines = output.strip().split('\n')
        for line in lines:
            if 'Bit Rate' in line:
                # "Bit Rate=54 Mb/s" 형태에서 속도 추출
                bit_rate_match = re.search(r'Bit Rate[=:]\s*(\d+(?:\.\d+)?)\s*([MGK]b/s)', line)
                if bit_rate_match:
                    speed_value = float(bit_rate_match.group(1))
                    speed_unit = bit_rate_match.group(2)
                    
                    # 단위를 bps로 변환
                    if speed_unit == 'Gb/s':
                        speed_bps = speed_value * 1_000_000_000
                    elif speed_unit == 'Mb/s':
                        speed_bps = speed_value * 1_000_000
                    elif speed_unit == 'Kb/s':
                        speed_bps = speed_value * 1_000
                    else:
                        speed_bps = speed_value
                    
                    return speed_bps
        
        # iwconfig에서 속도 정보를 찾지 못한 경우 대안 방법
        speed_file = f"/sys/class/net/{interface_name}/speed"
        if os.path.exists(speed_file):
            with open(speed_file, 'r') as f:
                speed_mbps = int(f.read().strip())
                return speed_mbps * 1_000_000  # Mbps를 bps로 변환
        
        # 속도 정보를 찾을 수 없는 경우 오류 발생
        raise ValueError(f"무선 네트워크 인터페이스 '{interface_name}'의 속도 정보를 찾을 수 없습니다.")
        
    except subprocess.CalledProcessError as e:
        raise ValueError(f"네트워크 인터페이스 '{interface_name}'에 대한 iwconfig 명령어 실행에 실패했습니다: {str(e)}")
    except Exception as e:
        raise ValueError(f"무선 네트워크 용량을 가져오는 중 오류가 발생했습니다: {str(e)}")

def _get_wired_capacity_linux(interface_name):
    """
    Linux에서 유선 네트워크 인터페이스의 최대 대역폭을 가져옵니다.
    """
    try:
        # 유선 인터페이스인 경우 ethtool 사용
        cmd = f"ethtool {interface_name}"
        result = subprocess.run(cmd, shell=True, capture_output=True, encoding='utf-8')
        
        if result.returncode != 0:
            # stderr에 경고가 있어도 stdout은 정상일 수 있음
            if "Operation not permitted" in result.stderr:
                # 경고 메시지가 있지만 계속 진행
                pass
            else:
                raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
        
        output = result.stdout
        
        # 출력에서 Speed 정보 추출
        lines = output.strip().split('\n')
        for line in lines:
            if 'Speed:' in line:
                speed_str = line.split(':')[1].strip()
                if speed_str and speed_str != '':
                    try:
                        # ethtool은 보통 "1000Mb/s" 형태로 반환
                        if 'Mb/s' in speed_str:
                            speed_mbps = int(speed_str.replace('Mb/s', ''))
                            return speed_mbps * 1_000_000  # Mbps를 bps로 변환
                        elif 'Gb/s' in speed_str:
                            speed_gbps = int(speed_str.replace('Gb/s', ''))
                            return speed_gbps * 1_000_000_000  # Gbps를 bps로 변환
                        else:
                            # 숫자만 추출 (Mbps로 가정)
                            speed_mbps = int(''.join(filter(str.isdigit, speed_str)))
                            return speed_mbps * 1_000_000  # Mbps를 bps로 변환
                        
                    except ValueError:
                        raise ValueError(f"네트워크 인터페이스 '{interface_name}'의 속도 정보를 파싱할 수 없습니다: {speed_str}")
        
        # ethtool에서 속도 정보를 찾지 못한 경우 /sys/class/net 확인
        speed_file = f"/sys/class/net/{interface_name}/speed"
        if os.path.exists(speed_file):
            with open(speed_file, 'r') as f:
                speed_mbps = int(f.read().strip())
                return speed_mbps * 1_000_000  # Mbps를 bps로 변환
        
        # Speed 정보를 찾을 수 없는 경우 오류 발생
        raise ValueError(f"네트워크 인터페이스 '{interface_name}'의 속도 정보를 찾을 수 없습니다.")
        
    except subprocess.CalledProcessError as e:
        raise ValueError(f"네트워크 인터페이스 '{interface_name}'에 대한 ethtool 명령어 실행에 실패했습니다: {str(e)}")
    except Exception as e:
        raise ValueError(f"유선 네트워크 용량을 가져오는 중 오류가 발생했습니다: {str(e)}")