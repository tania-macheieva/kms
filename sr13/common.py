import re,json
ART={'the','a','an','this','these','that','those','its','their','his','her','some','all','each','any','our','your','certain','several','of','and'}
def norm(x):
    x=x.lower().replace('`','').replace('*','').replace('_',' ')
    x=re.sub(r"[\"'“”’()\[\],;:]"," ",x); x=re.sub(r'\s+',' ',x).strip()
    w=x.split()
    while w and w[0] in ART: w=w[1:]
    return ' '.join(w).rstrip('.')
def toks(x): return {t for t in norm(x).split() if t not in ART}
def lenient_eq(a,b):
    A,B=toks(a),toks(b)
    if not A or not B: return False
    if A<=B or B<=A: return True
    return len(A&B)/len(A|B)>=0.5
def match_strict(p,g): return tuple(norm(x) for x in p)==tuple(norm(x) for x in g)
def match_len(p,g): return p[1]==g[1] and lenient_eq(p[0],g[0]) and lenient_eq(p[2],g[2])
def score(preds,gold,match):
    TP=FP=FN=0
    for sid,g in gold.items():
        P=[tuple(t) for t in preds.get(sid,[])]; used=set()
        tp=0
        for gi in g:
            for k,p in enumerate(P):
                if k not in used and match(p,gi): used.add(k); tp+=1; break
        TP+=tp; FP+=len(P)-tp; FN+=len(g)-tp
    pr=TP/(TP+FP) if TP+FP else 0; rc=TP/(TP+FN) if TP+FN else 0
    f=2*pr*rc/(pr+rc) if pr+rc else 0
    return dict(TP=TP,FP=FP,FN=FN,P=pr,R=rc,F1=f)
