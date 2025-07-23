import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import argparse
matplotlib.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 깨짐 방지

def plot_backlog(n_samples=None, save_plot=True):
    # 파일 경로
    results_dir = os.path.join(os.path.dirname(__file__), '../results')
    latest_result = max([os.path.join(results_dir, d) for d in os.listdir(results_dir)], key=os.path.getmtime)
    csv_path = os.path.join(latest_result, 'backlog/total_backlog.csv')

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
    plt.plot(time, df['sum_GFLOPs'], label='Total GFLOPs/ms')
    plt.plot(time, df['avg_GFLOPs'], label='Average GFLOPs/ms')
    plt.ylabel('GFLOPs/ms')
    plt.xlabel('Time step')
    plt.title('전체 연산량 분석: 총합 및 평균 GFLOPs')
    plt.legend()
    plt.tight_layout()
    
    if save_plot:
        plt.savefig(os.path.join(os.path.dirname(__file__), 'total_gflops.png'))
        plt.clf()
    else:
        plt.show()

    plt.figure(figsize=(14, 6))
    plt.plot(time, df['sum_KB'], label='Total KB/ms')
    plt.plot(time, df['avg_KB'], label='Average KB/ms')
    plt.ylabel('KB/ms')
    plt.xlabel('Time step')
    plt.title('전체 데이터 전송량 분석: 총합 및 평균 KB')
    plt.legend()
    plt.tight_layout()
    
    if save_plot:
        plt.savefig(os.path.join(os.path.dirname(__file__), 'total_kb.png'))
        plt.clf()
    else:
        plt.show()

    # GFLOPs/ms (계산) 플롯
    plt.figure(figsize=(14, 6))
    for col in gflops_cols:
        plt.plot(time, df[col], label=f"{col} (GFLOPs/ms)")
    plt.ylabel('Backlog (GFLOPs/ms)')
    plt.xlabel('Time step')
    plt.title('노드별 연산 처리량 분석: 시간에 따른 백로그 변화')
    plt.legend()
    plt.tight_layout()
    
    if save_plot:
        plt.savefig(os.path.join(os.path.dirname(__file__), 'backlog_gflops.png'))
        plt.clf()
    else:
        plt.show()

    # KB/ms (전송) 플롯
    plt.figure(figsize=(14, 6))
    for col in kb_cols:
        plt.plot(time, df[col], label=f"{col} (KB/ms)")
    plt.ylabel('Backlog (KB/ms)')
    plt.xlabel('Time step')
    plt.title('노드 간 데이터 전송량 동향: 시간별 백로그 추이')
    plt.legend()
    plt.tight_layout()
    
    if save_plot:
        plt.savefig(os.path.join(os.path.dirname(__file__), 'backlog_kb.png'))
        plt.clf()
    else:
        plt.show()

    if save_plot:
        print('백로그 플롯이 plot/backlog_gflops.png, plot/backlog_kb.png, plot/total_gflops.png, plot/total_kb.png로 저장되었습니다.')

def plot_latency(n_samples=None, save_plot=True):
    # 파일 경로
    results_dir = os.path.join(os.path.dirname(__file__), '../results')
    latest_result = max([os.path.join(results_dir, d) for d in os.listdir(results_dir)], key=os.path.getmtime)
    latency_path = os.path.join(latest_result, 'latency/test job 1.csv')
    path_path = os.path.join(latest_result, 'path/path.csv')

    # latency 값 읽기
    latency_df = pd.read_csv(latency_path)
    if n_samples is not None:
        mid = len(latency_df) // 2
        half_samples = n_samples // 2
        latency_df = latency_df.iloc[mid-half_samples:mid+half_samples]
    latency_values = latency_df.iloc[:, 0].values  # 첫 번째 컬럼

    # path 값 읽기
    with open(path_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    paths = [line.strip() for line in lines[1:]]  # 첫 줄은 헤더
    if n_samples is not None:
        mid = len(paths) // 2
        half_samples = n_samples // 2
        paths = paths[mid-half_samples:mid+half_samples]

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
    for lat, p in zip(latency_values, paths):
        short = shorten_path(p)
        if short not in data_by_path:
            data_by_path[short] = []
        data_by_path[short].append(lat)

    # 경로별 latency boxplot
    plt.figure(figsize=(16, 8))
    labels = list(data_by_path.keys())
    data = [data_by_path[k] for k in labels]
    plt.boxplot(data, tick_labels=labels, vert=True, showmeans=True)
    plt.ylabel('Latency (ms)')
    plt.xlabel('Path')
    plt.title('작업 경로별 지연시간 패턴 분석: 분포도 기반 성능 비교')
    plt.xticks(rotation=30, fontsize=9)
    plt.tight_layout()
    
    if save_plot:
        plt.savefig(os.path.join(os.path.dirname(__file__), 'latency_by_path.png'))
        plt.clf()
        print('경로별 latency boxplot이 plot/latency_by_path.png로 저장되었습니다.')
    else:
        plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, help='분석할 샘플 수 (기본값: 전체)')
    parser.add_argument('--show', action='store_true', help='화면에 플롯 표시 (기본값: 파일로 저장)')
    args = parser.parse_args()

    plot_backlog(n_samples=args.samples, save_plot=not args.show)
    plot_latency(n_samples=args.samples, save_plot=not args.show)