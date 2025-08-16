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
    plt.plot(time, df['sum_actual_queue_backlog (KB)'], label='Total Actual Queue Backlog', color=Colors.TOTAL, linestyle='--')
    plt.plot(time, df['avg_actual_queue_backlog (KB)'], label='Average Actual Queue Backlog', color=Colors.AVERAGE, linestyle='--')
    
    plt.ylabel('Actual Queue Backlog (KB)')
    plt.xlabel('Time step')
    plt.title('Actual Queue Backlog 분석')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    save_or_show_plot(plot_dir, f'actual_queue_backlog_{file_postfix}.svg', save_plot)

def plot_computing_performance(result_dir: str, file_postfix: str, start_idx: int = 0, 
                             end_idx: Optional[int] = None, save_plot: bool = True):
    """연산 성능 분석"""
    plot_dir, result_dir_name = create_plot_dir(result_dir)
    
    df, time = load_performance_data(result_dir, start_idx, end_idx)
    if df is None:
        return

    plt.figure(figsize=(12, 6), dpi=300)
    
    # 노드별 컴퓨팅 성능 (있는 경우만)
    computing_cols = [col for col in df.columns if '(computing)' in col]
    for col in computing_cols:
        node_num = col.split('.')[-1].split('(')[0]  # IP 마지막 숫자
        plt.plot(time, df[col], label=f"Node {node_num}", color=Colors.NODES[node_num])
    
    # 전체/평균 컴퓨팅 성능
    plt.plot(time, df['sum_computing (GFLOPs/s)'], label='Total Computing', color=Colors.TOTAL, linestyle='--')
    plt.plot(time, df['avg_computing (GFLOPs/s)'], label='Average Computing', color=Colors.AVERAGE, linestyle='--')
    
    plt.ylabel('Computing Performance (GFLOPs/s)')
    plt.xlabel('Time step')
    plt.title('연산량 분석')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    save_or_show_plot(plot_dir, f'computing_performance_{result_dir_name}{file_postfix}.svg', save_plot)

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
        
        print(f"성능 분석 완료: {os.path.basename(result_dir)}") 