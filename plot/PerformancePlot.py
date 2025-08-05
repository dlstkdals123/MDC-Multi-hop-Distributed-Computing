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

def plot_network_backlog(result_dir: str, file_postfix: str, start_idx: int = 0, 
                        end_idx: Optional[int] = None, save_plot: bool = True):
    """네트워크 백로그 분석"""
    plot_dir, result_dir_name = create_plot_dir(result_dir)
    
    df, time = load_performance_data(result_dir, start_idx, end_idx)
    if df is None:
        return

    plt.figure(figsize=(12, 6), dpi=300)
    
    # 노드별 백로그
    backlog_cols = [col for col in df.columns if '(actual_queue_backlog)' in col]
    for col in backlog_cols:
        node_num = col.split('.')[-1].split('(')[0]  # IP 마지막 숫자
        plt.plot(time, df[col], label=f"Node {node_num}", color=Colors.NODES[node_num])
    
    # 전체/평균 백로그
    plt.plot(time, df['sum_actual_queue_backlog (KB/s)'], label='Total Backlog', color=Colors.TOTAL, linestyle='--')
    plt.plot(time, df['avg_actual_queue_backlog (KB/s)'], label='Average Backlog', color=Colors.AVERAGE, linestyle='--')
    
    plt.ylabel('Queue Backlog (KB/s)')
    plt.xlabel('Time step')
    plt.title('네트워크 백로그 분석: 노드별/전체/평균 큐 백로그')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    save_or_show_plot(plot_dir, f'network_backlog_{result_dir_name}{file_postfix}.svg', save_plot)

def plot_computing_performance(result_dir: str, file_postfix: str, start_idx: int = 0, 
                             end_idx: Optional[int] = None, save_plot: bool = True):
    """연산 성능 분석"""
    plot_dir, result_dir_name = create_plot_dir(result_dir)
    
    df, time = load_performance_data(result_dir, start_idx, end_idx)
    if df is None:
        return

    plt.figure(figsize=(12, 6), dpi=300)
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
    save_or_show_plot(plot_dir, f'computing_performance_{result_dir_name}{file_postfix}.svg', save_plot)

def plot_packet_drops(result_dir: str, file_postfix: str, start_idx: int = 0, 
                     end_idx: Optional[int] = None, save_plot: bool = True):
    """패킷 드롭 분석"""
    plot_dir, result_dir_name = create_plot_dir(result_dir)
    
    df, time = load_performance_data(result_dir, start_idx, end_idx)
    if df is None:
        return

    # 입력 패킷 드롭
    plt.figure(figsize=(12, 6), dpi=300)
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
    save_or_show_plot(plot_dir, f'packet_drops_input_{result_dir_name}{file_postfix}.svg', save_plot)

    # 출력 패킷 드롭
    plt.figure(figsize=(12, 6), dpi=300)
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
    save_or_show_plot(plot_dir, f'packet_drops_output_{result_dir_name}{file_postfix}.svg', save_plot)

if __name__ == "__main__":
    results_dir = os.path.join(os.path.dirname(__file__), '../results')
    result_dirs = [os.path.join(results_dir, d) for d in os.listdir(results_dir)]

    start_idx = 0
    end_idx = None
    save_plot = True

    start_str = f'_{start_idx}' if start_idx != 0 else ''
    end_str = f'_{end_idx}' if end_idx is not None else ''
    file_postfix = f'{start_str}{end_str}'

    for result_dir in result_dirs:
        print(f"\n{os.path.basename(result_dir)} 성능 분석 중...")
        
        # 기본 성능 분석
        plot_network_backlog(result_dir, file_postfix, start_idx, end_idx, save_plot)
        plot_computing_performance(result_dir, file_postfix, start_idx, end_idx, save_plot)
        plot_packet_drops(result_dir, file_postfix, start_idx, end_idx, save_plot)
        
        print(f"성능 분석 완료: {os.path.basename(result_dir)}") 