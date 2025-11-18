import os
import glob
import argparse
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def parse_trace(path, bin_size=0.1):
    flows={}
    max_time=0.0
    with open(path,'r',encoding='utf-8',errors='ignore') as f:
        for line in f:
            parts=line.strip().split()
            if not parts:
                continue
            ev=parts[0]
            if ev not in ('s','r','d'):
                continue
            try:
                t=float(parts[1])
            except:
                continue
            max_time=max(max_time,t)
            pkt_type=parts[4] if len(parts)>4 else ''
            try:
                size=int(parts[5])
            except:
                size=0
            fid=parts[7] if len(parts)>7 else '0'
            key=(pkt_type,fid)
            if key not in flows:
                flows[key]={'sent_pkts':0,'sent_bytes':0,'recv_pkts':0,'recv_bytes':0,'recv_events':[]}
            if ev=='s':
                flows[key]['sent_pkts']+=1
                flows[key]['sent_bytes']+=size
            elif ev=='r':
                flows[key]['recv_pkts']+=1
                flows[key]['recv_bytes']+=size
                flows[key]['recv_events'].append((t,size))
    duration=max_time if max_time>0 else 1.0
    for k,v in flows.items():
        bins=int(math.ceil(duration/bin_size))
        ts=np.zeros(bins)
        for t,size in v['recv_events']:
            idx=int(t/bin_size)
            if idx>=bins:
                idx=bins-1
            ts[idx]+=size*8.0/1e6/bin_size
        v['throughput_ts']=ts
        v['duration']=duration
    return flows

def metrics_from_flows(flows):
    rows=[]
    for (pkt_type,fid),v in flows.items():
        if pkt_type in ('tcp','cbr','ack'):
            goodput_mbps=(v['recv_bytes']*8.0/1e6)/v['duration'] if v['duration']>0 else 0.0
            plr_pct=0.0
            if v['sent_pkts']>0:
                plr_pct=(1.0 - (v['recv_pkts']/v['sent_pkts']))*100.0
            rows.append({'flow':f'{pkt_type}-{fid}','pkt_type':pkt_type,'fid':fid,'goodput_mbps':goodput_mbps,'plr_pct':plr_pct})
    return pd.DataFrame(rows)

def jain_fairness(flows):
    series=[]
    for (pkt_type,fid),v in flows.items():
        if pkt_type=='tcp':
            ts=v['throughput_ts']
            n=len(ts)
            if n==0:
                continue
            start=int(n*2/3)
            tail=ts[start:]
            m=tail.mean() if len(tail)>0 else ts.mean()
            series.append(m)
    if not series:
        return 1.0
    s=np.array(series)
    num=(s.sum()**2)
    den=len(s)*( (s**2).sum() )
    return float(num/den) if den>0 else 0.0

def stability_cov(flows):
    agg=None
    for (pkt_type,fid),v in flows.items():
        ts=v['throughput_ts']
        if agg is None:
            agg=ts.copy()
        else:
            agg=agg+ts
    if agg is None or agg.mean()==0:
        return 0.0
    return float(agg.std()/agg.mean())

def find_variant_traces(traces_dir):
    patterns={'cubic':'*cubic*.tr','reno':'*reno*.tr','yeah':'*yeah*.tr','vegas':'*vegas*.tr'}
    found={}
    for name,pat in patterns.items():
        files=glob.glob(os.path.join(traces_dir,pat))
        if files:
            found[name]=sorted(files)[0]
    return found

def plot_partA(df_metrics,out_dir):
    os.makedirs(out_dir,exist_ok=True)
    df=df_metrics.copy()
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    order=['cubic','reno','yeah','vegas']
    gp=[]
    pl=[]
    labels=[]
    for v in order:
        sub=df[df['variant']==v]
        gp.append(sub['goodput_mbps'].sum())
        pl.append(sub['plr_pct'].mean() if len(sub)>0 else 0)
        labels.append(v)
    axs[0].bar(labels,gp,color=['#4e79a7','#f28e2b','#e15759','#76b7b2'])
    axs[0].set_ylabel('Goodput (Mbps)')
    axs[1].bar(labels,pl,color=['#4e79a7','#f28e2b','#e15759','#76b7b2'])
    axs[1].set_ylabel('PLR (%)')
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir,'partA_goodput_plr.png'),dpi=150)

def partA(traces_dir,out_dir):
    variants=find_variant_traces(traces_dir)
    rows=[]
    fairness_rows=[]
    stability_rows=[]
    for vname,trace in variants.items():
        flows=parse_trace(trace)
        df=metrics_from_flows(flows)
        df['variant']=vname
        rows.append(df)
        fairness_rows.append({'variant':vname,'jain_index':jain_fairness(flows)})
        stability_rows.append({'variant':vname,'cov':stability_cov(flows)})
    if not rows:
        return
    metrics=pd.concat(rows,ignore_index=True)
    os.makedirs(out_dir,exist_ok=True)
    metrics.to_csv(os.path.join(out_dir,'partA_metrics.csv'),index=False)
    pd.DataFrame(fairness_rows).to_csv(os.path.join(out_dir,'partA_fairness.csv'),index=False)
    pd.DataFrame(stability_rows).to_csv(os.path.join(out_dir,'partA_stability.csv'),index=False)
    plot_partA(metrics,out_dir)

def partB(drop_dir,red_dir,out_dir):
    vd_drop=find_variant_traces(drop_dir)
    vd_red=find_variant_traces(red_dir)
    rows=[]
    for label,vd in [('DropTail',vd_drop),('RED',vd_red)]:
        for vname,trace in vd.items():
            flows=parse_trace(trace)
            df=metrics_from_flows(flows)
            df['queue']=label
            df['variant']=vname
            df['jain_index']=jain_fairness(flows)
            df['cov']=stability_cov(flows)
            rows.append(df)
    if not rows:
        return
    df=pd.concat(rows,ignore_index=True)
    os.makedirs(out_dir,exist_ok=True)
    df.to_csv(os.path.join(out_dir,'partB_metrics.csv'),index=False)
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    for i,(metric,label) in enumerate([('goodput_mbps','Goodput (Mbps)'),('plr_pct','PLR (%)')]):
        piv=df.pivot_table(index='variant',columns='queue',values=metric,aggfunc='sum').reindex(['cubic','reno','yeah','vegas'])
        axs[i].bar(piv.index,piv['DropTail'],label='DropTail',alpha=0.7)
        axs[i].bar(piv.index,piv['RED'],label='RED',alpha=0.7)
        axs[i].set_ylabel(label)
        axs[i].legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir,'partB_comparison.png'),dpi=150)

def partC(traces,out_dir):
    series=[]
    for t in traces:
        flows=parse_trace(t)
        agg=None
        for v in flows.values():
            ts=v['throughput_ts']
            agg=ts if agg is None else agg+ts
        if agg is None:
            continue
        series.append(agg)
    if not series:
        return
    m=np.mean(np.stack(series),axis=0)
    s=np.std(np.stack(series),axis=0,ddof=1)
    se=s/ math.sqrt(len(series))
    ci=1.96*se
    os.makedirs(out_dir,exist_ok=True)
    pd.DataFrame({'mean':m,'ci95':ci}).to_csv(os.path.join(out_dir,'partC_mean_ci.csv'),index=False)
    plt.figure(figsize=(8,4))
    x=np.arange(len(m))
    plt.plot(x,m,label='Mean Throughput')
    plt.fill_between(x,m-ci,m+ci,alpha=0.3,label='95% CI')
    plt.ylabel('Mbps')
    plt.xlabel('Time bins')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir,'partC_mean_ci.png'),dpi=150)

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest='cmd')
    a=sub.add_parser('partA')
    a.add_argument('--traces-dir',required=True)
    a.add_argument('--out-dir',required=True)
    b=sub.add_parser('partB')
    b.add_argument('--drop-dir',required=True)
    b.add_argument('--red-dir',required=True)
    b.add_argument('--out-dir',required=True)
    c=sub.add_parser('partC')
    c.add_argument('--traces',nargs='+',required=True)
    c.add_argument('--out-dir',required=True)
    args=p.parse_args()
    if args.cmd=='partA':
        partA(args.traces_dir,args.out_dir)
    elif args.cmd=='partB':
        partB(args.drop_dir,args.red_dir,args.out_dir)
    elif args.cmd=='partC':
        partC(args.traces,args.out_dir)

if __name__=='__main__':
    main()
