import os
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional
from PlotUtil import Colors, create_plot_dir, save_or_show_plot

def load_data(result_dir: str, start_idx: int = 0, end_idx: Optional[int] = None):
    csv_path = os.path.join(result_dir, 'backlog/total_backlog.csv')
    if not os.path.exists(csv_path):
        print(f"백로그 파일이 없습니다: {csv_path}")
        return None, None
        
    df = pd.read_csv(csv_path)
    end_idx = len(df) if end_idx is None else end_idx
    df = df.iloc[start_idx:end_idx]
    time = range(start_idx, len(df) + start_idx)
    return df, time

def plot_node_gflops(result_dir: str, start_idx: int = 0,
                    end_idx: Optional[int] = None, save_plot: bool = True):
    plot_dir, result_dir_name = create_plot_dir(result_dir)
    
    df, time = load_data(result_dir, start_idx, end_idx)
    if df is None:
        return

    node_cols = [col for col in df.columns if '->' in col]
    compute_cols = [col for col in node_cols if col.split('->')[0] == col.split('->')[1]]

    plt.figure(figsize=(14, 6))
    plt.plot(time, df['sum_GFLOPs'], label='Total GFLOPs', color=Colors.TOTAL, 
             linestyle='--', linewidth=1, alpha=0.5)
    plt.plot(time, df['avg_GFLOPs'], label='Average GFLOPs', color=Colors.AVERAGE,
             linestyle='--', linewidth=1, alpha=0.5)
    
    for col in compute_cols:
        node_num = col.split('->')[0].split('.')[-1]
        plt.plot(time, df[col], label=f"{col} (GFLOPs)", color=Colors.NODES[node_num])
    
    plt.ylabel('Backlog (GFLOPs)')
    plt.xlabel('Time step')
    plt.title('노드별 연산 처리량 분석: 시간에 따른 백로그 변화')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    save_or_show_plot(plot_dir, f'backlog_gflops_{result_dir_name}.svg', save_plot)

def plot_node_kb(result_dir: str, start_idx: int = 0,
                 end_idx: Optional[int] = None, save_plot: bool = True):
    plot_dir, result_dir_name = create_plot_dir(result_dir)
    
    df, time = load_data(result_dir, start_idx, end_idx)
    if df is None:
        return

    node_cols = [col for col in df.columns if '->' in col]
    transfer_cols = [col for col in node_cols if col.split('->')[0] != col.split('->')[1]]

    plt.figure(figsize=(14, 6))
    plt.plot(time, df['sum_KB'], label='Total KB', color=Colors.TOTAL, 
             linestyle='--', linewidth=1, alpha=0.5)
    plt.plot(time, df['avg_KB'], label='Average KB', color=Colors.AVERAGE,
             linestyle='--', linewidth=1, alpha=0.5)
    
    for col in transfer_cols:
        node_num = col.split('->')[0].split('.')[-1]
        plt.plot(time, df[col], label=f"{col} (KB)", color=Colors.NODES[node_num])
    
    plt.ylabel('Backlog (KB)')
    plt.xlabel('Time step')
    plt.title('노드 간 데이터 전송량 분석: 시간에 따른 백로그 변화')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    save_or_show_plot(plot_dir, f'backlog_kb_{result_dir_name}.svg', save_plot)

if __name__ == "__main__":
    results_dir = os.path.join(os.path.dirname(__file__), '../results')
    result_dirs = [os.path.join(results_dir, d) for d in os.listdir(results_dir)]

    start_idx = 0
    end_idx = None
    save_plot = True

    for result_dir in result_dirs:
        print(f"\n{os.path.basename(result_dir)} 분석 중...")
        plot_node_gflops(result_dir, start_idx, end_idx, save_plot)
        plot_node_kb(result_dir, start_idx, end_idx, save_plot)