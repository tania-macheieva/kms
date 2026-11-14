import json
from common import *
R=json.load(open('gold.json')); G={r['id']:r['gold'] for r in R}; SENT={r['id']:r['sentence'] for r in R}
P={'rules':json.load(open('rules_out.json'))['preds'],'spacy':json.load(open('spacy_out.json'))['preds'],
   'llm':{x['id']:[(t['s'],t['p'],t['o']) for t in x['triples']] for x in json.load(open('llm_out.json'))}}
E={}
for m,p in P.items():
    E[m]=[]
    for sid,g in G.items():
        pr=[tuple(t) for t in p.get(sid,[])]; used=set(); mg=set()
        for gi,gg in enumerate(g):
            for k,x in enumerate(pr):
                if k not in used and match_len(x,gg): used.add(k); mg.add(gi); break
        for k,x in enumerate(pr):
            if k not in used: E[m].append(('FP',sid,x,None))
        for gi,gg in enumerate(g):
            if gi not in mg: E[m].append(('FN',sid,None,tuple(gg)))
json.dump(E,open('errors.json','w'),ensure_ascii=False,indent=1)
import sys
for m in sys.argv[1:]:
    print('=====',m,len(E[m]))
    for t,sid,x,g in E[m]: print(t,sid,'PRED',x,'GOLD',g)
