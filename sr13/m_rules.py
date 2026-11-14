import re,json,time
LEX={'uses':['use','uses','requires','require','depends on','run','runs'],
 'produces':['produces','produce','outputs','output','generates','generate','creates','create'],
 'supports':['supports','support','allows','allow','accepts','accept'],
 'contains':['contains','contain','includes','include','stores','store'],
 'performs':['performs','perform']}
V={v:p for p,vs in LEX.items() for v in vs}
BOUND={',',';','(',')',':','when','if','that','which','while','because','then','by','default','so','but','and','or','to','for','in','on','with','from','using','as','of','at','are','is','be','can','will','may','also','only','not'}
def clean(s): return re.sub(r'[`*_]','',s)
def words(s): return re.findall(r"[A-Za-z0-9_.\-/+'’]+|[,;:()]",s)
def left(w,i):
    out=[]
    for t in reversed(w[:i]):
        if t.lower() in BOUND: break
        out.append(t)
        if len(out)==5: break
    return ' '.join(reversed(out))
def right(w,j):
    out=[]
    for t in w[j:]:
        if t.lower() in BOUND and out: break
        if t.lower() in BOUND: continue
        out.append(t)
        if len(out)==6: break
    return ' '.join(out)
def extract(sent):
    s=clean(sent); w=words(s); T=[]
    for i,t in enumerate(w):
        tl=t.lower()
        # passive agent: X is/are used|produced|... by Y
        m=re.match(r'(used|produced|generated|created|performed|supported)$',tl)
        if m and i+2<len(w) and w[i+1].lower()=='by' and i>0 and w[i-1].lower() in ('is','are','was','were'):
            p={'used':'uses','produced':'produces','generated':'produces','created':'produces','performed':'performs','supported':'supports'}[tl]
            a=right(w,i+2); o=left(w,i-1)
            if a and o: T.append((a,p,o))
            continue
        if tl in ('is','are') and i+1<len(w) and w[i+1].lower() in ('a','an'):
            sub=left(w,i); ob=right(w,i+2)
            if sub and ob: T.append((sub,'is_a',ob))
            continue
        two=(tl+' '+w[i+1].lower()) if i+1<len(w) else ''
        if two=='depends on': p='uses'; j=i+2
        elif tl in V and tl not in ('output','use','run','create','support','include','store','contain','perform','allow','accept','require','generate','produce'): p=V[tl]; j=i+1
        elif tl in V and i>0 and w[i-1].lower() in ('will','can','may','also','not'): p=V[tl]; j=i+1
        else: continue
        sub=left(w,i); ob=right(w,j)
        if sub and ob: T.append((sub,p,ob))
    return T
if __name__=='__main__':
    S=json.load(open('sentences_only.json')); t0=time.time()
    out={x['id']:extract(x['sentence']) for x in S}; dt=time.time()-t0
    json.dump({'time_s':dt,'preds':out},open('rules_out.json','w'),ensure_ascii=False,indent=1)
    print(sum(len(v) for v in out.values()),'triples',round(dt*1000,1),'ms')
