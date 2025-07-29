import os
import pandas as pd
import matplotlib.pyplot as plt
import re
from typing import Optional, Tuple, List, Dict
from PlotUtil import Colors, create_plot_dir, save_or_show_plot

def load_latency_data(result_dir: str, start_idx: int = 0, end_idx: Optional[int] = None) -> Tuple[List[float], List[str]]:
    """지연시간과 경로 데이터를 로드합니다."""
    latency_path = os.path.join(result_dir, 'latency/test job 1.csv')
    path_path = os.path.join(result_dir, 'path/path.csv')
    
    if not os.path.exists(latency_path) or not os.path.exists(path_path):
        print(f"지연시간 또는 경로 파일이 없습니다: {result_dir}")
        return [], []

    # 지연시간 데이터 로드
    latency_df = pd.read_csv(latency_path)
    end_idx = len(latency_df) if end_idx is None else end_idx
    latency_df = latency_df.iloc[start_idx:end_idx]
    latency_values = latency_df.iloc[:, 0].values
    
    # 경로 데이터 로드
    with open(path_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    paths = [line.strip() for line in lines[1:]]  # 첫 줄은 헤더
    paths = paths[start_idx:end_idx]
    
    # 300초 이상 필터링
    filtered_data = [(lat, path) for lat, path in zip(latency_values, paths) if lat < 300000]
    
    if not filtered_data:
        print("필터링 후 데이터가 없습니다.")
        return [], []
    
    return zip(*filtered_data)

def shorten_path(path: str) -> str:
    """경로를 축약된 형태로 변환합니다."""
    items = [p.strip() for p in path.split(',') if p.strip()]
    short_items = []
    
    for item in items:
        if 'transmission' in item:
            # 전송 경로: IP->IP 형태를 축약
            ips = re.findall(r'\d+\.\d+\.\d+\.(\d+)->\d+\.\d+\.\d+\.(\d+)', item)
            if ips:
                short_items.append(f'{ips[0][0]}→{ips[0][1]}')
        elif 'computing' in item:
            # 컴퓨팅 경로: IP 형태를 축약
            ip = re.search(r'(\d+\.\d+\.\d+\.(\d+))', item)
            if ip:
                short_items.append(f'C{ip.group(2)}')
    
    return '-'.join(short_items)

def group_latency_by_path(latency_values: List[float], paths: List[str]) -> Dict[str, List[float]]:
    """경로별로 지연시간을 그룹화합니다."""
    data_by_path = {}
    
    for lat, path in zip(latency_values, paths):
        short_path = shorten_path(path)
        if short_path not in data_by_path:
            data_by_path[short_path] = []
        data_by_path[short_path].append(lat)
    
    return data_by_path

def plot_latency_by_path(result_dir: str, start_idx: int = 0,
                        end_idx: Optional[int] = None, save_plot: bool = True):
    """경로별 지연시간을 박스플롯으로 시각화합니다."""
    plot_dir, result_dir_name = create_plot_dir(result_dir)
    
    # 데이터 로드
    latency_values, paths = load_latency_data(result_dir, start_idx, end_idx)
    if not latency_values:
        return
    
    # 경로별 그룹화
    data_by_path = group_latency_by_path(latency_values, paths)
    
    if not data_by_path:
        print("그룹화할 데이터가 없습니다.")
        return
    
    # 경로별로 정렬 (알파벳 순)
    sorted_paths = sorted(data_by_path.keys())
    
    # 박스플롯 생성
    plt.figure(figsize=(16, 8))
    labels = sorted_paths
    data = [data_by_path[k] for k in labels]
    
    # 박스플롯 스타일 설정
    boxprops = dict(color=Colors.TOTAL, linewidth=1.5)
    whiskerprops = dict(color=Colors.TOTAL, linewidth=1.5)
    flierprops = dict(marker='o', markerfacecolor=Colors.TOTAL, markersize=4, alpha=0.7)
    medianprops = dict(color='red', linewidth=2)
    meanprops = dict(marker='D', markerfacecolor=Colors.AVERAGE, markersize=8, markeredgecolor='black')
    
    # 박스플롯 그리기
    plt.boxplot(data, labels=labels, vert=True, showmeans=True,
                boxprops=boxprops, whiskerprops=whiskerprops, flierprops=flierprops,
                medianprops=medianprops, meanprops=meanprops)
    
    # 그래프 스타일링
    plt.ylabel('지연시간 (ms)', fontsize=12)
    plt.xlabel('경로', fontsize=12)
    plt.title('작업 경로별 지연시간 패턴 분석: 분포도 기반 성능 비교', fontsize=14, pad=20)
    plt.xticks(rotation=30, fontsize=9)
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    save_or_show_plot(plot_dir, f'latency_by_path_{result_dir_name}.svg', save_plot)

def plot_latency_over_time(result_dir: str, start_idx: int = 0,
                          end_idx: Optional[int] = None, save_plot: bool = True):
    """시간에 따른 지연시간 변화를 라인 플롯으로 시각화합니다."""
    plot_dir, result_dir_name = create_plot_dir(result_dir)
    
    # 데이터 로드
    latency_values, paths = load_latency_data(result_dir, start_idx, end_idx)
    if not latency_values:
        return
    
    # 시간 축 생성
    time = range(len(latency_values))
    
    # 경로별로 데이터 분리
    path_groups = {}
    for i, (lat, path) in enumerate(zip(latency_values, paths)):
        short_path = shorten_path(path)
        if short_path not in path_groups:
            path_groups[short_path] = {'time': [], 'latency': []}
        path_groups[short_path]['time'].append(i)
        path_groups[short_path]['latency'].append(lat)
    
    # 라인 플롯 생성
    plt.figure(figsize=(14, 6))
    
    # 각 경로별로 라인 그리기
    for i, (path_name, data) in enumerate(path_groups.items()):
        color = Colors.NODES.get(str(i % len(Colors.NODES) + 1), Colors.TOTAL)
        plt.plot(data['time'], data['latency'], label=path_name, color=color, linewidth=1)
    
    # 평균 지연시간 라인 추가
    mean_latency = sum(latency_values) / len(latency_values)
    plt.axhline(mean_latency, color=Colors.AVERAGE, linestyle='--', linewidth=1, alpha=0.5,
                label=f'평균: {mean_latency:.1f}ms')
    
    # 그래프 스타일링
    plt.ylabel('지연시간 (ms)', fontsize=12)
    plt.xlabel('시간 단계', fontsize=12)
    plt.title('시간에 따른 지연시간 변화 분석', fontsize=14, pad=20)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    save_or_show_plot(plot_dir, f'latency_over_time_{result_dir_name}.svg', save_plot)

if __name__ == "__main__":
    results_dir = os.path.join(os.path.dirname(__file__), '../results')
    
    if not os.path.exists(results_dir):
        print(f"결과 디렉토리가 없습니다: {results_dir}")
        exit()
    
    result_dirs = [os.path.join(results_dir, d) for d in os.listdir(results_dir) 
                   if os.path.isdir(os.path.join(results_dir, d))]
    
    start_idx = 0
    end_idx = None
    save_plot = True
    
    for result_dir in result_dirs:
        print(f"\n{os.path.basename(result_dir)} 분석 중...")
        plot_latency_by_path(result_dir, start_idx, end_idx, save_plot)
        plot_latency_over_time(result_dir, start_idx, end_idx, save_plot)