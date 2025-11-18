#!/usr/bin/env python3
import argparse, os
from collections import defaultdict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def parse_trace(path, delta=0.2):
    """读取 NS2 trace，返回 Goodput(Mbps)、PLR(%)、吞吐时间序列"""
    send_bytes = recv_bytes = send_pkts = recv_pkts = 0
    last_time = 0.0
    buckets = defaultdict(int)     # key = 时间桶编号, value = bits

    with open(path) as f:
        for line in f:
            if line.startswith('#') or line.strip() == '':
                continue
            parts = line.split()
            event = parts[0]          # r / + / -
            t     = float(parts[1])   # 时间 (s)
            size  = int(parts[5])     # 第 6 列是 packet size (Byte)
            if event == '+':          # 发送
                send_pkts  += 1
                send_bytes += size
            elif event == 'r':        # 接收
                recv_pkts  += 1
                recv_bytes += size
                buckets[int(t // delta)] += size * 8   # bits
                last_time = max(last_time, t)

    goodput = (recv_bytes * 8) / last_time / 1e6       # Mbps
    plr     = (send_pkts - recv_pkts) / send_pkts * 100
    max_idx = int(last_time // delta) + 1
    ts = np.array([buckets[i] / 1e6 / delta for i in range(max_idx)])  # Mbps
    return goodput, plr, ts

def jain(xs):
    xs = np.array(xs)
    return (xs.sum() ** 2) / (len(xs) * (xs ** 2).sum())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('traces', nargs=4,
        help='trace files: cubic reno yeah vegas')
    parser.add_argument('-o', '--out', default='partA_fig.png')
    args = parser.parse_args()

    algos = ['cubic', 'reno', 'yeah', 'vegas']
    results = {}
    for algo, path in zip(algos, args.traces):
        g, p, ts = parse_trace(path)
        results[algo] = {'goodput': g, 'plr': p, 'ts': ts}

    # 打印表格
    df = pd.DataFrame({k: {'Goodput(Mbps)': v['goodput'],
                           'PLR(%)':        v['plr']}
                       for k, v in results.items()}).T
    print('\n===== Per-flow metrics =====')
    print(df.round(3))

    # 绘图
    import matplotlib
    matplotlib.use('Agg')       # 无需弹窗
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].bar(algos, df['Goodput(Mbps)']); ax[0].set_title('Goodput (Mbps)')
    ax[1].bar(algos, df['PLR(%)']);        ax[1].set_title('Packet Loss Rate (%)')
    plt.tight_layout(); plt.savefig(args.out)
    print(f'\n已保存比较图: {args.out}')

    # Jain 公平性（后 1/3）
    fairness = {a: jain(v['ts'][len(v['ts'])*2//3:]) for a, v in results.items()}
    print('\nJain Fairness (last 1/3):')
    for a, val in fairness.items():
        print(f' {a:6s}: {val:.4f}')

    # 稳定性 CoV
    stability = {a: v['ts'].std() / v['ts'].mean() for a, v in results.items()}
    print('\nThroughput Coefficient of Variation (CoV):')
    for a, val in stability.items():
        print(f' {a:6s}: {val:.4f}')

if __name__ == '__main__':
    main()#!/usr/bin/env python3
import argparse, os
from collections import defaultdict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def parse_trace(path, delta=0.2):
    """读取 NS2 trace，返回 Goodput(Mbps)、PLR(%)、吞吐时间序列"""
    send_bytes = recv_bytes = send_pkts = recv_pkts = 0
    last_time = 0.0
    buckets = defaultdict(int)     # key = 时间桶编号, value = bits

    with open(path) as f:
        for line in f:
            if line.startswith('#') or line.strip() == '':
                continue
            parts = line.split()
            event = parts[0]          # r / + / -
            t     = float(parts[1])   # 时间 (s)
            size  = int(parts[5])     # 第 6 列是 packet size (Byte)
            if event == '+':          # 发送
                send_pkts  += 1
                send_bytes += size
            elif event == 'r':        # 接收
                recv_pkts  += 1
                recv_bytes += size
                buckets[int(t // delta)] += size * 8   # bits
                last_time = max(last_time, t)

    goodput = (recv_bytes * 8) / last_time / 1e6       # Mbps
    plr     = (send_pkts - recv_pkts) / send_pkts * 100
    max_idx = int(last_time // delta) + 1
    ts = np.array([buckets[i] / 1e6 / delta for i in range(max_idx)])  # Mbps
    return goodput, plr, ts

def jain(xs):
    xs = np.array(xs)
    return (xs.sum() ** 2) / (len(xs) * (xs ** 2).sum())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('traces', nargs=4,
        help='trace files: cubic reno yeah vegas')
    parser.add_argument('-o', '--out', default='partA_fig.png')
    args = parser.parse_args()

    algos = ['cubic', 'reno', 'yeah', 'vegas']
    results = {}
    for algo, path in zip(algos, args.traces):
        g, p, ts = parse_trace(path)
        results[algo] = {'goodput': g, 'plr': p, 'ts': ts}

    # 打印表格
    df = pd.DataFrame({k: {'Goodput(Mbps)': v['goodput'],
                           'PLR(%)':        v['plr']}
                       for k, v in results.items()}).T
    print('\n===== Per-flow metrics =====')
    print(df.round(3))

    # 绘图
    import matplotlib
    matplotlib.use('Agg')       # 无需弹窗
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].bar(algos, df['Goodput(Mbps)']); ax[0].set_title('Goodput (Mbps)')
    ax[1].bar(algos, df['PLR(%)']);        ax[1].set_title('Packet Loss Rate (%)')
    plt.tight_layout(); plt.savefig(args.out)
    print(f'\n已保存比较图: {args.out}')

    # Jain 公平性（后 1/3）
    fairness = {a: jain(v['ts'][len(v['ts'])*2//3:]) for a, v in results.items()}
    print('\nJain Fairness (last 1/3):')
    for a, val in fairness.items():
        print(f' {a:6s}: {val:.4f}')

    # 稳定性 CoV
    stability = {a: v['ts'].std() / v['ts'].mean() for a, v in results.items()}
    print('\nThroughput Coefficient of Variation (CoV):')
    for a, val in stability.items():
        print(f' {a:6s}: {val:.4f}')

if __name__ == '__main__':
    main()
