import re, collections
def parse(fn):
    terms={}; cur=None
    for line in open(fn):
        line=line.rstrip('\n')
        if line=='[Term]': cur={'is_a':[],'syn':[]}; continue
        if line.startswith('[') : cur=None; continue
        if cur is None or not line: continue
        k,_,v=line.partition(': ')
        if k=='id': cur['id']=v; terms[v]=cur
        elif k=='name': cur['name']=v
        elif k=='def': cur['def']=v.split('"')[1] if '"' in v else v
        elif k=='is_a': cur['is_a'].append(v.split(' ! ')[0])
        elif k=='is_obsolete': cur['obs']=True
        elif k=='relationship': cur.setdefault('rel',[]).append(v)
    return {i:t for i,t in terms.items() if not t.get('obs')}
T=parse('so.obo')
ch=collections.defaultdict(list)
for i,t in T.items():
    for p in t['is_a']: ch[p].append(i)
def desc(r):
    out=set();st=[r]
    while st:
        x=st.pop()
        for c in ch[x]:
            if c not in out: out.add(c);st.append(c)
    return out
