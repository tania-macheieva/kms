"""Крок 1: запустити RAG із recorder-LLM і записати промпти, яких немає в кеші -> llm_log/in/gen_SR11.json"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LAB11_ROOT=ROOT.parent/'lab11_repo'
if not (LAB11_ROOT/'src'/'rag.py').is_file():
    raise FileNotFoundError(f'Локальне джерело RAG не знайдено: {LAB11_ROOT}')
sys.path.insert(0,str(LAB11_ROOT))
from src.rag import RAG, Config
from src.graph_context import GraphContextBuilder
from src.llm import ReplayLLM, key_of
from src import evalrag as E
rec=E.Recorder(ReplayLLM(E.GEN_MODEL,cache_dir=ROOT/'data'/'llm_cache')); rag=RAG(rec,graph=GraphContextBuilder(),log=False)
T=[json.loads(l) for l in open(ROOT/'eval/sr11_tests.jsonl',encoding='utf-8')]; FX={f['id']:f for f in json.load(open(ROOT/'eval/sr11_fixtures.json'))}
for t in T: rag.ask(t['question'],t['role'],Config(name='SR11',rerank=True),qid=t['id'],extra_chunks=[FX[i] for i in t.get('fixtures',[])])
u={}
for x in rec.todo: u[key_of(E.GEN_MODEL,x['system'],x['user'])]=x
items=[dict(id=f'SR11-{i:03d}',key=k,user=v['user']) for i,(k,v) in enumerate(u.items(),1)]
out=ROOT/'llm_log/in/gen_SR11.json'; out.parent.mkdir(parents=True,exist_ok=True)
with open(out,'w',encoding='utf-8') as f:
    json.dump(dict(system=next(iter(u.values()))['system'],items=items),f,ensure_ascii=False,indent=1)
print(len(items),'prompts')
