import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import argparse
matplotlib.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 깨짐 방지

# 색상 정의
TOTAL_COLOR = '#1f77b4'  # 파란색
AVG_COLOR = '#ff7f0e'    # 주황색
NODE_COLORS = {
    '1': '#2ca02c',   # 초록색
    '2': '#d62728',   # 빨간색
    '3': '#9467bd',   # 보라색
    '4': '#8c564b',   # 갈색
    '5': '#e377c2',   # 분홍색
    '6': '#7f7f7f',   # 회색
    '7': '#bcbd22',   # 연두색
    '8': '#17becf'    # 청록색
}

def plot_backlog(result_dir, n_samples=None, save_plot=True):
    # 파일 경로
    csv_path = os.path.join(result_dir, 'backlog/total_backlog.csv')
    if not os.path.exists(csv_path):
        print(f"백로그 파일이 없습니다: {csv_path}")
        return

    # 결과 저장 디렉토리 생성
    result_dir_name = os.path.basename(result_dir)
    samples_str = f"_samples{n_samples}" if n_samples is not None else ""
    plot_dir = os.path.join(os.path.dirname(__file__), f'plots_{result_dir_name}')
    os.makedirs(plot_dir, exist_ok=True)

    # CSV 파일 읽기
    df = pd.read_csv(csv_path)
    
    # n_samples가 지정된 경우 중간에서 n개 선택
    if n_samples is not None:
        mid = len(df) // 2
        half_samples = n_samples // 2
        df = df.iloc[mid-half_samples:mid+half_samples]
        time = range(mid-half_samples, mid+half_samples)  # 실제 time step 유지
    else:
        time = range(len(df))

    # 헤더에서 노드쌍 컬럼만 추출
    node_columns = [col for col in df.columns if '->' in col]

    # 계산 노드와 전송 노드 분리
    gflops_cols = [col for col in node_columns if col.split('->')[0] == col.split('->')[1]]
    kb_cols = [col for col in node_columns if col.split('->')[0] != col.split('->')[1]]

    # 전체 GFLOPs/KB 플롯
    plt.figure(figsize=(14, 6))
    plt.plot(time, df['sum_GFLOPs'], label='Total GFLOPs', color=TOTAL_COLOR)
    plt.plot(time, df['avg_GFLOPs'], label='Average GFLOPs', color=AVG_COLOR)
    plt.ylabel('GFLOPs')
    plt.xlabel('Time step')
    plt.title('전체 연산량 분석: 총합 및 평균 GFLOPs')
    plt.legend()
    plt.tight_layout()
    
    if save_plot:
        plt.savefig(os.path.join(plot_dir, f'total_gflops_{result_dir_name}{samples_str}.png'))
        plt.clf()
    else:
        plt.show()

    plt.figure(figsize=(14, 6))
    plt.plot(time, df['sum_KB'], label='Total KB', color=TOTAL_COLOR)
    plt.plot(time, df['avg_KB'], label='Average KB', color=AVG_COLOR)
    plt.ylabel('KB')
    plt.xlabel('Time step')
    plt.title('전체 데이터 전송량 분석: 총합 및 평균 KB')
    plt.legend()
    plt.tight_layout()
    
    if save_plot:
        plt.savefig(os.path.join(plot_dir, f'total_kb_{result_dir_name}{samples_str}.png'))
        plt.clf()
    else:
        plt.show()

    # GFLOPs/ms (계산) 플롯
    plt.figure(figsize=(14, 6))
    for col in gflops_cols:
        node = col.split('->')[0] # 노드 이름 (ex: 192.168.1.5)
        node_num = node.split('.')[-1]  # IP 주소의 마지막 숫자
        plt.plot(time, df[col], label=f"{node} (GFLOPs)", color=NODE_COLORS[node_num])
    plt.ylabel('Backlog (GFLOPs)')
    plt.xlabel('Time step')
    plt.title('노드별 연산 처리량 분석: 시간에 따른 백로그 변화')
    plt.legend()
    plt.tight_layout()
    
    if save_plot:
        plt.savefig(os.path.join(plot_dir, f'backlog_gflops_{result_dir_name}{samples_str}.png'))
        plt.clf()
    else:
        plt.show()

    # KB/ms (전송) 플롯
    plt.figure(figsize=(14, 6))
    for col in kb_cols:
        node_num = col.split('->')[0].split('.')[-1]  # 시작 노드의 IP 마지막 숫자
        plt.plot(time, df[col], label=f"{col} (KB)", color=NODE_COLORS[node_num])
    plt.ylabel('Backlog (KB)')
    plt.xlabel('Time step')
    plt.title('노드 간 데이터 전송량 동향: 시간별 백로그 추이')
    plt.legend()
    plt.tight_layout()
    
    if save_plot:
        plt.savefig(os.path.join(plot_dir, f'backlog_kb_{result_dir_name}{samples_str}.png'))
        plt.clf()
    else:
        plt.show()

    if save_plot:
        print(f'백로그 플롯이 plots_{result_dir_name} 폴더에 저장되었습니다.')

def plot_latency(result_dir, n_samples=None, save_plot=True):
    # 파일 경로
    latency_path = os.path.join(result_dir, 'latency/test job 1.csv')
    path_path = os.path.join(result_dir, 'path/path.csv')
    
    if not os.path.exists(latency_path) or not os.path.exists(path_path):
        print(f"지연시간 또는 경로 파일이 없습니다: {result_dir}")
        return

    # 결과 저장 디렉토리 생성
    result_dir_name = os.path.basename(result_dir)
    samples_str = f"_samples{n_samples}" if n_samples is not None else ""
    plot_dir = os.path.join(os.path.dirname(__file__), f'plots_{result_dir_name}')
    os.makedirs(plot_dir, exist_ok=True)

    # latency 값 읽기
    latency_df = pd.read_csv(latency_path)
    latency_values = latency_df.iloc[:, 0].values  # 첫 번째 컬럼

    # path 값 읽기
    with open(path_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    paths = [line.strip() for line in lines[1:]]  # 첫 줄은 헤더

    # n_samples가 지정된 경우 중앙에서 n개 선택
    if n_samples is not None:
        mid = len(latency_values) // 2
        half_samples = n_samples // 2
        start_idx = max(0, mid - half_samples)
        end_idx = min(len(latency_values), mid + half_samples)
        
        latency_values = latency_values[start_idx:end_idx]
        paths = paths[start_idx:end_idx]

    def shorten_path(path):
        import re
        items = [p.strip() for p in path.split(',') if p.strip()]
        short = []
        for item in items:
            if 'transmission' in item:
                ips = re.findall(r'\d+\.\d+\.\d+\.(\d+)->\d+\.\d+\.\d+\.(\d+)', item)
                if ips:
                    short.append(f'{ips[0][0]}→{ips[0][1]}')
            elif 'computing' in item:
                ip = re.search(r'(\d+\.\d+\.\d+\.(\d+))', item)
                if ip:
                    short.append(f'C{ip.group(2)}')
        return '-'.join(short)

    # 경로별로 latency 그룹화 (축약 label 사용)
    data_by_path = {}
    path_stats = {}  # 각 경로별 통계 정보 저장
    
    for lat, p in zip(latency_values, paths):
        short = shorten_path(p)
        if short not in data_by_path:
            data_by_path[short] = []
            path_stats[short] = {'total': 0, 'valid': 0}
        
        path_stats[short]['total'] += 1
        if not (pd.isna(lat) or lat == '' or str(lat).strip() == ''):
            data_by_path[short].append(lat)
            path_stats[short]['valid'] += 1

    # 시간에 따른 latency 변화 그래프
    plt.figure(figsize=(16, 8))
    
    # n_samples가 지정된 경우 실제 시간 인덱스 유지
    if n_samples is not None:
        mid = len(latency_df.iloc[:, 0].values) // 2
        half_samples = n_samples // 2
        start_idx = max(0, mid - half_samples)
        end_idx = min(len(latency_df.iloc[:, 0].values), mid + half_samples)
        time_steps = range(start_idx, end_idx)
    else:
        time_steps = range(len(latency_values))
    
    # 경로별로 다른 색상 사용
    path_colors = {}
    color_idx = 0
    for path in set(paths):
        short_path = shorten_path(path)
        if short_path not in path_colors:
            path_colors[short_path] = list(NODE_COLORS.values())[color_idx % len(NODE_COLORS)]
            color_idx += 1
    
    # 각 경로별로 선 그래프 그리기
    for i, (lat, path) in enumerate(zip(latency_values, paths)):
        if not (pd.isna(lat) or lat == '' or str(lat).strip() == ''):
            short_path = shorten_path(path)
            plt.scatter(time_steps[i], lat, color=path_colors[short_path], alpha=0.6, s=20)
    
    # 경로별 범례 추가
    legend_elements = []
    for short_path, color in path_colors.items():
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                        markerfacecolor=color, markersize=8, label=short_path))
    
    plt.legend(handles=legend_elements, loc='upper right', fontsize=8)
    plt.ylabel('Latency (ms)')
    plt.xlabel('Time step')
    plt.title('시간에 따른 지연시간 변화: 경로별 실시간 성능 모니터링')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    if save_plot:
        plt.savefig(os.path.join(plot_dir, f'latency_time_series_{result_dir_name}{samples_str}.png'))
        plt.clf()
    else:
        plt.show()

    # 경로별 latency boxplot
    plt.figure(figsize=(16, 8))
    labels = list(data_by_path.keys())
    data = [data_by_path[k] for k in labels]
    
    # boxplot 색상 설정
    boxprops = dict(color=TOTAL_COLOR)
    whiskerprops = dict(color=TOTAL_COLOR)
    flierprops = dict(marker='o', markerfacecolor=TOTAL_COLOR, markersize=4)
    medianprops = dict(color='red')
    meanprops = dict(marker='D', markerfacecolor=AVG_COLOR, markersize=8)
    
    bp = plt.boxplot(data, tick_labels=labels, vert=True, showmeans=True,
                     boxprops=boxprops, whiskerprops=whiskerprops, flierprops=flierprops,
                     medianprops=medianprops, meanprops=meanprops, showfliers=False)
    
    # 각 경로별 통계 정보를 boxplot 위에 표시
    for i, (label, stats) in enumerate(path_stats.items()):
        total = stats['total']
        valid = stats['valid']
        missing_rate = (total - valid) / total * 100 if total > 0 else 0
        
        # boxplot 위에 텍스트 추가
        plt.text(i+1, plt.gca().get_ylim()[1] * 1.02, 
                f'n={valid}/{total}\n({missing_rate:.1f}% 결측)', 
                ha='center', va='bottom', fontsize=8,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7))
    
    plt.ylabel('Latency (ms)')
    plt.xlabel('Path')
    plt.title('작업 경로별 지연시간 패턴 분석: 분포도 기반 성능 비교')
    plt.xticks(rotation=30, fontsize=9)
    plt.tight_layout()
    
    if save_plot:
        plt.savefig(os.path.join(plot_dir, f'latency_by_path_{result_dir_name}{samples_str}.png'))
        plt.clf()
        print(f'Latency 분석 그래프들이 plots_{result_dir_name} 폴더에 저장되었습니다.')
    else:
        plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, help='분석할 샘플 수 (기본값: 전체)')
    parser.add_argument('--show', action='store_true', help='화면에 플롯 표시 (기본값: 파일로 저장)')
    args = parser.parse_args()

    results_dir = os.path.join(os.path.dirname(__file__), '../results')
    result_dirs = [os.path.join(results_dir, d) for d in os.listdir(results_dir)]
    
    for result_dir in result_dirs:
        print(f"\n{os.path.basename(result_dir)} 분석 중...")
        plot_backlog(result_dir, n_samples=args.samples, save_plot=not args.show)
        plot_latency(result_dir, n_samples=args.samples, save_plot=not args.show)