#!/usr/bin/env python3
"""Метрики якості знань для KMS «Domain Knowledge Hub» (ЛР11): 688 фрагментів + манифест + граф + прогони оцінювання.
Запуск: python3 kms_quality.py --data data --as-of 2026-11-12 --out snap/s1.json   (лише стандартна бібліотека)"""
import json,csv,re,glob,os,argparse,zlib,datetime as dt
REQ=['chunk_id','doc_id','title','section','type','date','sensitivity','lang','source_url']
CONS=['title','type','date','sensitivity','lang','source_url']
def ws(s): return re.sub(r'\s+',' ',s).strip()
def load(data):
    C=[json.loads(l) for l in open(f'{data}/corpus.jsonl',encoding='utf-8')]
    M={m['doc_id']:m for m in json.load(open(f'{data}/docs_manifest.json',encoding='utf-8'))}
    return C,M
def m1_completeness(C,M):
    bad=[c['chunk_id'] for c in C if any(not str(c.get(k) or '').strip() for k in REQ) or not str(M.get(c['doc_id'],{}).get('license') or '').strip()]
    return 1-len(bad)/len(C),bad
def m2_accuracy(C,data):
    docs={};bad=[]
    for c in C:
        p=f"{data}/docs_clean/{c['doc_id']}.md"
        if c['doc_id'] not in docs: docs[c['doc_id']]=open(p,encoding='utf-8').read() if os.path.exists(p) else None
        d=docs[c['doc_id']]; body=c['text'].split('\n',1)[1] if '\n' in c['text'] else c['text']
        if d is None or ws(body)!=ws(d[c['start']:c['end']]): bad.append(c['chunk_id'])
    return 1-len(bad)/len(C),bad
def shingles(t,k=5):
    w=re.findall(r'\w+',t.lower()); return {zlib.crc32(" ".join(w[i:i+k]).encode()) for i in range(max(1,len(w)-k+1))}
def m3_uniqueness(C,thr=0.9):
    S=[shingles(c['text'].split('\n',1)[-1]) for c in C]; dup=set(); pairs=[]
    for i in range(len(C)):
        for j in range(i+1,len(C)):
            a,b=S[i],S[j]
            if not a or not b: continue
            if len(a&b)/len(a|b)>=thr: dup.add(j); pairs.append((C[i]['chunk_id'],C[j]['chunk_id']))
    return 1-len(dup)/len(C),pairs
def graph_refs(data):
    nodes={};rels=[]
    for f in glob.glob(f'{data}/graph/nodes_*.csv'):
        t=os.path.basename(f)[6:-4]; r=list(csv.reader(open(f,encoding='utf-8')))
        nodes[t]={row[0] for row in r[1:] if row}
    for f in glob.glob(f'{data}/graph/rels_*.csv'):
        n=os.path.basename(f)[5:-4]; rel,ends=n.split('__'); a,b=ends.split('_',1)
        for row in csv.DictReader(open(f,encoding='utf-8')): rels.append((rel,a,b,row['from'],row['to']))
    return nodes,rels
def m4_consistency(C,M,data):
    refs=0;bad=[]
    for c in C:                       # фрагмент -> манифест: існує документ і поля збігаються
        m=M.get(c['doc_id']); 
        for k in CONS:
            refs+=1
            if m is None or str(m.get(k))!=str(c.get(k)): bad.append((c['chunk_id'],k))
    nodes,rels=graph_refs(data)
    for rel,a,b,f,t in rels:          # ребро графа -> вузли
        for side,typ,v in (('from',a,f),('to',b,t)):
            refs+=1
            if v not in nodes.get(typ,set()): bad.append((f'{rel}:{f}->{t}',side))
    return 1-len(bad)/refs,bad,refs,len(rels)
def m5_timeliness(M,as_of,window=90):
    ages=[(as_of-dt.date.fromisoformat(m['date'])).days for m in M.values()]
    old=[d for d,a in zip(M,ages) if a>window]
    ages.sort(); return 1-len(old)/len(M),old,ages[len(ages)//2]
def eval_runs(data,C):
    ids={c['chunk_id'] for c in C}
    jl=lambda f:{json.loads(l)['id']:json.loads(l) for l in open(f,encoding='utf-8')}
    T=jl(f'{data}/eval/rag_eval.jsonl'); ST=jl(f'{data}/eval/sr11_tests.jsonl')
    RUNS={'A':('results_A.json',T,'2026-10-31'),'B':('results_B.json',T,'2026-11-01'),'SR11':('sr11_results.json',ST,'2026-11-11')}
    out={};retrieved=set()
    for k,(rf,tests,day) in RUNS.items():
        rows=json.load(open(f'{data}/eval/{rf}',encoding='utf-8'));J={j['id'].split(':',1)[1]:j for j in json.load(open(f'{data}/eval/judge_{k}_out.json',encoding='utf-8'))}
        cl=sup=tot=hit=0
        for r in rows:
            t=tests[r['id']]; g=len(t.get('gold_evidence',[]))+len(t.get('gold_ids',[]))
            if r['context_recall'] is not None: tot+=g; hit+=round(r['context_recall']*g)
            cs=J[r['id']]['claims']; cl+=len(cs); sup+=sum(c['verdict']=='supported' for c in cs)
            retrieved|=set(r.get('context_ids',[]))&ids
        out[k]=dict(date=day,faithfulness=sup/cl,claims=cl,context_recall=hit/tot,gold=tot,n=len(rows),utilisation_cum=len(retrieved)/len(ids))
    return out
def compute(data,as_of):
    C,M=load(data); v={}; d={}
    v['M1'],d['M1']=m1_completeness(C,M); v['M2'],d['M2']=m2_accuracy(C,data); v['M3'],d['M3']=m3_uniqueness(C)
    v['M4'],d['M4'],refs,nrel=m4_consistency(C,M,data); v['M5'],d['M5'],med=m5_timeliness(M,as_of)
    E=eval_runs(data,C); last=list(E.values())[-1]
    v['M6']=last['faithfulness']; v['M7']=last['context_recall']; v['M8']=last['utilisation_cum']
    return dict(as_of=str(as_of),n_chunks=len(C),n_docs=len(M),n_refs=refs,n_graph_rels=nrel,median_age_days=med,metrics=v,defects={k:(x[:10] if isinstance(x,list) else x) for k,x in d.items()},defect_counts={k:len(x) for k,x in d.items()},runs=E)
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--data',default='data'); ap.add_argument('--as-of',default=str(dt.date.today())); ap.add_argument('--out'); a=ap.parse_args()
    r=compute(a.data,dt.date.fromisoformat(a.as_of)); s=json.dumps(r,ensure_ascii=False,indent=1)
    if a.out: open(a.out,'w',encoding='utf-8').write(s)
    print(json.dumps(r['metrics'],indent=1)); print(r['defect_counts'],r['n_refs'],r['median_age_days']); print(json.dumps(r['runs'],indent=0)[:600])
