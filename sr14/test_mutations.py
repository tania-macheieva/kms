#!/usr/bin/env python3
"""Чи реагують метрики на навмисно внесені дефекти? (перевірка «метрика відображає якість»)."""
import json,shutil,sys,datetime as dt,tempfile
from pathlib import Path
sys.path.insert(0,'.'); import kms_quality as q
base='data_s2'; as_of=dt.date(2026,11,12); res=[]
def rw(tmp,fn):
    p=Path(tmp)/'corpus.jsonl'
    C=[json.loads(l) for l in p.open(encoding='utf-8')]
    fn(C)
    with p.open('w',encoding='utf-8') as f:
        f.write(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in C))
b=q.compute(base,as_of)['metrics']
def case(name,mut,metric):
    with tempfile.TemporaryDirectory(prefix='sr14_mut_') as tmp:
        shutil.copytree(base,tmp,dirs_exist_ok=True)
        mut(Path(tmp))
        m=q.compute(tmp,as_of)['metrics']
        res.append((name,metric,b[metric],m[metric],m[metric]<b[metric]))
case('50 фрагментів без source_url',lambda p:rw(p,lambda C:[c.__setitem__('source_url','') for c in C[:50]]),'M1')
case('30 фрагментів: підмінено слово в тексті',lambda p:rw(p,lambda C:[c.__setitem__('text',c['text'].replace(' the ',' a ',1)+' extra') for c in C[:30]]),'M2')
case('40 фрагментів скопійовано (дублі)',lambda p:rw(p,lambda C:C.extend([dict(c,chunk_id=c['chunk_id']+'_dup') for c in C[:40]])),'M3')
case('60 фрагментів: sensitivity не збігається з манифестом',lambda p:rw(p,lambda C:[c.__setitem__('sensitivity','public' if c['sensitivity']!='public' else 'restricted') for c in C[:60]]),'M4')
def old_manifest(tmp):
    p=tmp/'docs_manifest.json'
    with p.open(encoding='utf-8') as f: M=json.load(f)
    [m.__setitem__('date','2026-05-01') for m in M[:15]]
    with p.open('w',encoding='utf-8') as f: json.dump(M,f,ensure_ascii=False)
case('15 документів із датою травня (>90 днів)',old_manifest,'M5')
out=[dict(case=n,metric=m,before=round(x,4),after=round(y,4),detected=bool(d)) for n,m,x,y,d in res]
json.dump(out,open('snap/mutation_tests.json','w'),ensure_ascii=False,indent=1)
for o in out: print(o)
assert all(o['detected'] for o in out)
