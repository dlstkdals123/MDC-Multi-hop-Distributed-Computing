import os
import matplotlib.pyplot as plt
import matplotlib
from typing import Optional, Tuple

# 한글 폰트 설정
matplotlib.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False

# 색상 상수 정의
class Colors:
    TOTAL = '#1f77b4'
    AVERAGE = '#ff7f0e'
    NODES = {
        '1': '#2ca02c', '2': '#d62728', '3': '#9467bd', '4': '#8c564b',
        '5': '#e377c2', '6': '#7f7f7f', '7': '#bcbd22', '8': '#17becf'
    }

def create_plot_dir(result_dir: str) -> Tuple[str, str]:
    result_dir_name = os.path.basename(result_dir)
    plot_dir = os.path.join(os.path.dirname(__file__), f'plots_{result_dir_name}')
    os.makedirs(plot_dir, exist_ok=True)
    return plot_dir, result_dir_name

def get_range_str(start_idx: int, end_idx: Optional[int]) -> str:
    start_str = f"_start{start_idx}" if start_idx > 0 else ""
    end_str = f"_end{end_idx}" if end_idx is not None else ""
    return f"{start_str}{end_str}"

def save_or_show_plot(plot_dir: str, filename: str, save_plot: bool):
    if save_plot:
        plt.savefig(os.path.join(plot_dir, filename), dpi=96, format='svg')
        plt.clf()
    else:
        plt.show()