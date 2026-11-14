"""Крок 2: прогін 20 тестів із відтворенням відповідей; результати -> eval/."""
import csv,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LAB11_ROOT=ROOT.parent/'lab11_repo'
if not (LAB11_ROOT/'src'/'rag.py').is_file():
    raise FileNotFoundError(f'Локальне джерело RAG не знайдено: {LAB11_ROOT}')
sys.path.insert(0,str(LAB11_ROOT))
from src.rag import RAG, Config
from src.graph_context import GraphContextBuilder
from src.llm import ReplayLLM
from src import evalrag as E
rag=RAG(ReplayLLM(E.GEN_MODEL,cache_dir=ROOT/'data'/'llm_cache'),graph=GraphContextBuilder(),log=False)
T=[json.loads(l) for l in open(ROOT/'eval/sr11_tests.jsonl',encoding='utf-8')]; FX={f['id']:f for f in json.load(open(ROOT/'eval/sr11_fixtures.json'))}
out=[]
for t in T:
    r=rag.ask(t['question'],t['role'],Config(name='SR11',rerank=True),qid=t['id'],extra_chunks=[FX[i] for i in t.get('fixtures',[])])
    m=E.auto_metrics(dict(t,category='injection' if t.get('comply') and t['subtype']=='indirect_injection' else t['category']),r,rag)
    m['category']=t['category']; m['subtype']=t['subtype']
    if t.get('comply') and t['subtype']=='access_bypass': m['complied']=re.search(t['comply'],r.answer,re.I) is not None
    m.update(question=t['question'],answer=r.answer,cited=r.cited,invalid=r.invalid_citations,guard=r.guard,context_ids=r.context_ids,sources=[(s['id'],s['kind'],s['doc_id'],s['sensitivity']) for s in r.sources],graph=r.graph,gold=[(e['doc_id'],e['start'],e['end']) for e in t.get('gold_evidence',[])],gold_ids=t.get('gold_ids',[]))
    out.append(m)
eval_dir=ROOT/'eval'
with open(eval_dir/'sr11_results.json','w',encoding='utf-8') as f:
    json.dump(out,f,ensure_ascii=False,indent=1)
columns=('id','category','subtype','role','expected','status','status_ok','context_recall','n_cited','n_invalid','uncited','retrieve_ms','graph_ms')
with open(eval_dir/'sr11_results.csv','w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore')
    writer.writeheader()
    writer.writerows(out)
for m in out: print(m['id'],m['category'],m['subtype'],'|',m['status'],'exp',m['expected'],'ok' if m['status_ok'] else 'FAIL','| ctxrec',m['context_recall'],'| inv',m['n_invalid'],'unc',m['uncited'],'|',m.get('injection_resisted'),m.get('complied'))
