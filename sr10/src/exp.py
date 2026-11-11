"""Експеримент СР10. python exp.py -> eval/results.json, eval/perq.json"""
import json, re, time, statistics, sys, os
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent)); import emb, metrics
from rank_bm25 import BM25Okapi
R=Path(__file__).resolve().parents[1]; (R/'cache').mkdir(exist_ok=True)
C=[json.loads(l) for l in open(R/'data/corpus.jsonl')]
G=[g for g in map(json.loads,open(R/'eval/gold_lab10.jsonl')) if g['answerable']]
PARA=dict(l.rstrip('\n').split('\t',1) for l in open(R/'eval/paraphrases.tsv'))
texts=[c['text'] for c in C]; spans=[(c['doc_id'],c['start'],c['end']) for c in C]
qs=[g['query'] for g in G]; pq=[PARA[g['qid']] for g in G]
def evaluate(S):  # S: (nq, nchunks) scores
    out=[]
    for i,g in enumerate(G):
        top=np.argsort(-S[i],kind='stable')[:10]; ranked=[spans[j] for j in top]
        m=metrics.all_metrics(ranked,g['evidence'])
        # ранг першого релевантного чанка
        full=[spans[j] for j in np.argsort(-S[i],kind='stable')[:100]]; gl=metrics.gains(full,g['evidence']); m['first_rank']=(gl.index(1)+1) if 1 in gl else None
        m['top5']=[C[j]['chunk_id'] for j in top[:5]]; out.append(m)
    return out
def summ(rows,idx=None):
    rows=[rows[i] for i in (idx if idx is not None else range(len(rows)))]
    return {k:round(float(np.mean([r[k] for r in rows])),4) for k in ('r5','mrr','ndcg')}|{'n':len(rows)}
def boot(rows,key='r5',B=2000,seed=0):
    v=np.array([r[key] for r in rows]); rng=np.random.default_rng(seed); b=[v[rng.integers(0,len(v),len(v))].mean() for _ in range(B)]
    return [round(float(np.percentile(b,2.5)),3),round(float(np.percentile(b,97.5)),3)]
res={'models':{}}; perq={}
sub={'en':[i for i,g in enumerate(G) if g['lang']=='en'],'uk':[i for i,g in enumerate(G) if g['lang']=='uk'],
     'uk_cross':[i for i,g in enumerate(G) if g['type']=='uk_cross'],'uk_internal':[i for i,g in enumerate(G) if g['type']=='uk_internal'],
     'keyword':[i for i,g in enumerate(G) if g['type']=='keyword'],'paraphrase':[i for i,g in enumerate(G) if g['type']=='paraphrase'],'multi_step':[i for i,g in enumerate(G) if g['type']=='multi_step']}
for name in ['minilm','bge','e5','potion']:
    m=emb.get(name); f=R/f'cache/{name}_corpus.npy'
    if f.exists(): P=np.load(f); t_idx=json.load(open(R/f'cache/{name}_t.json'))['t']
    else:
        t=time.perf_counter(); P=m.encode(texts); t_idx=time.perf_counter()-t; np.save(f,P); json.dump({'t':t_idx},open(R/f'cache/{name}_t.json','w'))
    Q=m.encode(qs,query=True); Q2=m.encode(pq,query=True)
    # затримка: один запит, 3 прогріви, потім медіана по 55 запитах (+ p95)
    for q in qs[:3]: m.encode([q],query=True)
    lat=[]
    for q in qs:
        t=time.perf_counter(); v=m.encode([q],query=True); s=P@v[0]; np.argsort(-s)[:10]; lat.append((time.perf_counter()-t)*1000)
    r=evaluate(Q@P.T); r2=evaluate(Q2@P.T); perq[name]=r; perq[name+'_para']=r2
    d=dict(note=m.note,dim=P.shape[1],index_mb=round(P.nbytes/1e6,2),model_mb=round(m.model_bytes/1e6,1),index_build_s=round(t_idx,1),
           lat_ms_median=round(statistics.median(lat),2),lat_ms_p95=round(sorted(lat)[int(.95*len(lat))-1],2),
           overall=summ(r),ci_r5=boot(r),by={k:summ(r,v) for k,v in sub.items()},para_overall=summ(r2),para_by={k:summ(r2,v) for k,v in sub.items()})
    if name in('minilm','e5'):  # вплив нормалізації: dot без нормалізації
        Pu=m.encode(texts,normalize=False) if not (R/f'cache/{name}_unnorm.npy').exists() else np.load(R/f'cache/{name}_unnorm.npy'); np.save(R/f'cache/{name}_unnorm.npy',Pu)
        Qu=m.encode(qs,query=True,normalize=False); d['unnormalized_dot']=summ(evaluate(Qu@Pu.T)); d['mean_norm_passages_unnorm']=round(float(np.linalg.norm(Pu,axis=1).mean()),2)
    res['models'][name]=d; print(name,d['overall'],d['lat_ms_median'],flush=True)
# BM25 (лексичний базовий)
tok=lambda s:re.findall(r'\w+',s.lower()); bm=BM25Okapi([tok(t) for t in texts])
def bm_scores(L): return np.array([bm.get_scores(tok(q)) for q in L])
lat=[]
for q in qs:
    t=time.perf_counter(); bm.get_scores(tok(q)); lat.append((time.perf_counter()-t)*1000)
r=evaluate(bm_scores(qs)); r2=evaluate(bm_scores(pq)); perq['bm25']=r; perq['bm25_para']=r2
res['models']['bm25']=dict(note='BM25Okapi (rank-bm25), не нейронна',dim=None,index_mb=None,model_mb=0,index_build_s=None,lat_ms_median=round(statistics.median(lat),2),lat_ms_p95=round(sorted(lat)[int(.95*len(lat))-1],2),overall=summ(r),ci_r5=boot(r),by={k:summ(r,v) for k,v in sub.items()},para_overall=summ(r2),para_by={k:summ(r2,v) for k,v in sub.items()})
res['n_queries']=len(G); res['n_chunks']=len(C); res['sub_sizes']={k:len(v) for k,v in sub.items()}
json.dump(res,open(R/'eval/results.json','w'),ensure_ascii=False,indent=1); json.dump(perq,open(R/'eval/perq.json','w'),ensure_ascii=False)
print('done')
