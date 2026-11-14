import json
from common import *
G={r['id']:r['gold'] for r in json.load(open('gold.json'))}
P={'Правила':json.load(open('rules_out.json'))['preds'],'spaCy':json.load(open('spacy_out.json'))['preds'],
   'LLM':{x['id']:[(t['s'],t['p'],t['o']) for t in x['triples']] for x in json.load(open('llm_out.json'))}}
res={}
print('gold',sum(map(len,G.values())),'triples;',sum(1 for v in G.values() if not v),'sentences without relations')
for m,p in P.items():
    st=score(p,G,match_strict); le=score(p,G,match_len)
    # predicate-agnostic lenient (S,O only)
    nopred=score(p,G,lambda a,b:lenient_eq(a[0],b[0]) and lenient_eq(a[2],b[2]))
    neg_fp=sum(len(p.get(s,[])) for s,g in G.items() if not g)
    res[m]=dict(strict=st,lenient=le,so_only=nopred,n_pred=sum(map(len,p.values())),fp_on_negative=neg_fp)
    print(m,'n_pred',res[m]['n_pred'],'| strict',{k:round(v,3) for k,v in st.items()},'| lenient',{k:round(v,3) for k,v in le.items()},'| S,O only F1',round(nopred['F1'],3),'| FP on no-relation sents',neg_fp)
json.dump(res,open('metrics.json','w'),indent=1)
# per predicate (lenient recall + precision)
for m,p in P.items():
    print(m)
    for pr in ['uses','produces','supports','is_a','contains','performs']:
        g={s:[t for t in v if t[1]==pr] for s,v in G.items()}; pp={s:[t for t in v if t[1]==pr] for s,v in p.items()}
        r=score(pp,g,match_len); print(' ',pr,'gold',sum(map(len,g.values())),'pred',sum(map(len,pp.values())),'TP',r['TP'],'P%.2f R%.2f F%.2f'%(r['P'],r['R'],r['F1']))
