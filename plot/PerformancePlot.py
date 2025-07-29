import os
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional
from PlotUtil import Colors, create_plot_dir, save_or_show_plot

def load_performance_data(result_dir: str, start_idx: int = 0, end_idx: Optional[int] = None):
    """성능 데이터 로드"""
    csv_path = os.path.join(result_dir, 'backlog/performance.csv')
    if not os.path.exists(csv_path):
        print(f"성능 파일이 없습니다: {csv_path}")
        return None, None
        
    df = pd.read_csv(csv_path)
    end_idx = len(df) if end_idx is None else end_idx
    df = df.iloc[start_idx:end_idx]
    time = range(start_idx, len(df) + start_idx)
    return df, time

def plot_network_throughput(result_dir: str, start_idx: int = 0, 
                          end_idx: Optional[int] = None, save_plot: bool = True):
    """네트워크 처리량 분석"""
    plot_dir, result_dir_name = create_plot_dir(result_dir)
    
    df, time = load_performance_data(result_dir, start_idx, end_idx)
    if df is None:
        return

    plt.figure(figsize=(14, 6))
    # 출력 - 입력 계산
    df['net_throughput'] = df['sum_output (KB/s)'] - df['sum_input (KB/s)']
    df['net_throughput_avg'] = df['avg_output (KB/s)'] - df['avg_input (KB/s)']
    
    plt.plot(time, df['net_throughput'], label='Total Net Throughput', color=Colors.TOTAL)
    plt.plot(time, df['net_throughput_avg'], label='Average Net Throughput', color=Colors.AVERAGE)
    plt.ylabel('Net Throughput (KB/s)')
    plt.xlabel('Time step')
    plt.title('네트워크 처리량 분석: 순 데이터 전송률 (출력-입력)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    save_or_show_plot(plot_dir, f'network_throughput_{result_dir_name}.svg', save_plot)

def plot_computing_performance(result_dir: str, start_idx: int = 0, 
                             end_idx: Optional[int] = None, save_plot: bool = True):
    """연산 성능 분석"""
    plot_dir, result_dir_name = create_plot_dir(result_dir)
    
    df, time = load_performance_data(result_dir, start_idx, end_idx)
    if df is None:
        return

    plt.figure(figsize=(14, 6))
    computing_cols = [col for col in df.columns if '(computing)' in col]
    for col in computing_cols:
        node_num = col.split('.')[-1].split('(')[0]  # IP 마지막 숫자
        plt.plot(time, df[col], label=f"{col}", color=Colors.NODES[node_num])
    plt.plot(time, df['sum_computing (GFLOPs/s)'], label='Total Computing', color=Colors.TOTAL, linestyle='--')
    plt.plot(time, df['avg_computing (GFLOPs/s)'], label='Average Computing', color=Colors.AVERAGE, linestyle='--')
    plt.ylabel('Computing Performance (GFLOPs/s)')
    plt.xlabel('Time step')
    plt.title('연산 성능 분석: 노드별/전체/평균 연산 능력')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    save_or_show_plot(plot_dir, f'computing_performance_{result_dir_name}.svg', save_plot)

def plot_packet_drops(result_dir: str, start_idx: int = 0, 
                     end_idx: Optional[int] = None, save_plot: bool = True):
    """패킷 드롭 분석"""
    plot_dir, result_dir_name = create_plot_dir(result_dir)
    
    df, time = load_performance_data(result_dir, start_idx, end_idx)
    if df is None:
        return

    # 입력 패킷 드롭
    plt.figure(figsize=(14, 6))
    dropped_input_cols = [col for col in df.columns if '(dropped_input)' in col]
    for col in dropped_input_cols:
        node_num = col.split('.')[-1].split('(')[0]  # IP 마지막 숫자
        plt.plot(time, df[col], label=f"{col}", color=Colors.NODES[node_num])
    plt.plot(time, df['sum_dropped_input (packet/s)'], label='Total Dropped Input', color=Colors.TOTAL, linestyle='--')
    plt.plot(time, df['avg_dropped_input (packet/s)'], label='Average Dropped Input', color=Colors.AVERAGE, linestyle='--')
    plt.ylabel('Dropped Input Packets (packet/s)')
    plt.xlabel('Time step')
    plt.title('입력 패킷 드롭 분석: 노드별/전체/평균')
    plt.ylim(bottom=0)  # y축 시작점을 0으로 고정
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    save_or_show_plot(plot_dir, f'packet_drops_input_{result_dir_name}.svg', save_plot)

    # 출력 패킷 드롭
    plt.figure(figsize=(14, 6))
    dropped_output_cols = [col for col in df.columns if '(dropped_output)' in col]
    for col in dropped_output_cols:
        node_num = col.split('.')[-1].split('(')[0]  # IP 마지막 숫자
        plt.plot(time, df[col], label=f"{col}", color=Colors.NODES[node_num])
    plt.plot(time, df['sum_dropped_output (packet/s)'], label='Total Dropped Output', color=Colors.TOTAL, linestyle='--')
    plt.plot(time, df['avg_dropped_output (packet/s)'], label='Average Dropped Output', color=Colors.AVERAGE, linestyle='--')
    plt.ylabel('Dropped Output Packets (packet/s)')
    plt.xlabel('Time step')
    plt.title('출력 패킷 드롭 분석: 노드별/전체/평균')
    plt.ylim(bottom=0)  # y축 시작점을 0으로 고정
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    save_or_show_plot(plot_dir, f'packet_drops_output_{result_dir_name}.svg', save_plot)

def plot_node_performance(result_dir: str, start_idx: int = 0, 
                         end_idx: Optional[int] = None, save_plot: bool = True):
    """노드별 성능 분석"""
    plot_dir, result_dir_name = create_plot_dir(result_dir)
    
    df, time = load_performance_data(result_dir, start_idx, end_idx)
    if df is None:
        return

    # 노드별 입출력 처리량 차이
    plt.figure(figsize=(14, 6))
    input_cols = [col for col in df.columns if '(input)' in col]
    output_cols = [col for col in df.columns if '(output)' in col]
    
    for in_col, out_col in zip(input_cols, output_cols):
        node_num = in_col.split('.')[-1].split('(')[0]  # IP 마지막 숫자
        diff = df[out_col] - df[in_col]  # 출력 - 입력
        plt.plot(time, diff, label=f"Node {node_num}", color=Colors.NODES[node_num])
        # 0 기준선 추가
        plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    
    plt.ylabel('Throughput Difference (KB/s)')
    plt.xlabel('Time step')
    plt.title('노드별 입출력 처리량 차이 분석 (출력 - 입력)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    save_or_show_plot(plot_dir, f'node_throughput_diff_{result_dir_name}.svg', save_plot)

if __name__ == "__main__":
    results_dir = os.path.join(os.path.dirname(__file__), '../results')
    result_dirs = [os.path.join(results_dir, d) for d in os.listdir(results_dir)]

    start_idx = 0
    end_idx = None
    save_plot = True

    for result_dir in result_dirs:
        print(f"\n{os.path.basename(result_dir)} 성능 분석 중...")
        
        # 기본 성능 분석
        plot_network_throughput(result_dir, start_idx, end_idx, save_plot)
        plot_computing_performance(result_dir, start_idx, end_idx, save_plot)
        plot_packet_drops(result_dir, start_idx, end_idx, save_plot)
        
        # 노드별 상세 분석
        plot_node_performance(result_dir, start_idx, end_idx, save_plot)
        
        print(f"성능 분석 완료: {os.path.basename(result_dir)}") 