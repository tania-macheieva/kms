import sys, json, re, collections, itertools, math
import numpy as np
sys.path.insert(0,'.')
from so_parse import T, ch, desc
from manual_tax import M, l1
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from scipy.cluster.hierarchy import linkage, fcluster
ROOT='SO:0001576'
ids=sorted(desc(ROOT), key=lambda x:T[x]['name']); N=len(ids); name2id={T[i]['name']:i for i in ids}
assert N>=60
# ---- еталон SO: L1 = нащадок-дитина кореня за першим батьком; L2 = перший безпосередній батько
def primary_path(i):
    p=[i]
    while p[-1]!=ROOT:
        par=[x for x in T[p[-1]]['is_a'] if x==ROOT or x in desc(ROOT)]
        p.append(par[0])
    return p
ref_l1={};ref_l2={}
for i in ids:
    p=primary_path(i); ref_l2[i]=p[1] if len(p)>1 else ROOT
    ref_l1[i]=p[-2] if len(p)>1 else i
multi=[i for i in ids if len([x for x in T[i]['is_a'] if x==ROOT or x in desc(ROOT)])>1]
# ---- ручна
man_l2={}
for k,v in M.items():
    for n in v:
        assert n in name2id,n; assert name2id[n] not in man_l2,n; man_l2[name2id[n]]=k
assert set(man_l2)==set(ids), set(T[i]['name'] for i in set(ids)-set(man_l2))
man_l1={i:l1(k) for i,k in man_l2.items()}
# ---- кластеризація знизу вгору
STOP=set("a an the of to in is are be that which this with by as at on or and for from has have it its into than then there whereby where".split())
def doc(i):
    n=re.sub(r'[_]+',' ',T[i]['name']); d=T[i].get('def','')
    d=re.sub(r'\(SO:\d+\)','',d)
    return (n+' ')*2+d
vec=TfidfVectorizer(lowercase=True,stop_words=list(STOP|{'sequence','variant'}),sublinear_tf=True,token_pattern=r"[A-Za-z0-9']+")
X=vec.fit_transform([doc(i) for i in ids]).toarray(); vocab=np.array(vec.get_feature_names_out())
from sklearn.metrics import silhouette_score
k1=len(set(man_l1.values())); k2=len(set(man_l2.values()))
# вибір зв'язування — за внутрішньою метрикою (silhouette, косинус), без звернення до еталона SO
LINK={}
for meth in ('average','complete','ward'):
    Zm=linkage(X,method=meth,metric='cosine' if meth!='ward' else 'euclidean')
    LINK[meth]=dict(Z=Zm,sil=(round(float(silhouette_score(X,fcluster(Zm,k1,'maxclust'),metric='cosine')),3) if len(set(fcluster(Zm,k1,'maxclust')))>1 else -1),
                    sizes=sorted(collections.Counter(fcluster(Zm,k1,'maxclust')).values(),reverse=True))
best=max(LINK,key=lambda m:LINK[m]['sil']); Z=LINK[best]['Z']
cl1=fcluster(Z,k1,'maxclust'); cl2=fcluster(Z,k2,'maxclust')
clu_l1={i:f"C{c}" for i,c in zip(ids,cl1)}; clu_l2={i:f"C{a}.{b}" for i,a,b in zip(ids,cl1,cl2)}
def cname(members_idx):
    c=X[members_idx].mean(0); top=vocab[np.argsort(-c)[:3]]; return ", ".join(top)
# ---- метрики
def parts(l1m,l2m): return l1m,l2m
def pair_f1(a,b):
    pa=set(); pb=set()
    for x,y in itertools.combinations(ids,2):
        if a[x]==a[y]: pa.add((x,y))
        if b[x]==b[y]: pb.add((x,y))
    tp=len(pa&pb); p=tp/len(pa) if pa else 0; r=tp/len(pb) if pb else 0
    return 2*p*r/(p+r) if p+r else 0
# дуги SO (у межах множини): батько→дитина
edges=[(p,i) for i in ids for p in T[i]['is_a'] if p in desc(ROOT) or p==ROOT]
def edge_pres(l1m):
    cnt=0;tot=0
    for p,c in edges:
        if p==ROOT: continue
        tot+=1; cnt+= l1m[p]==l1m[c] if p in l1m else 0
    return cnt/tot if tot else float('nan')
def ambiguous(l1m, thr):
    cats=sorted(set(l1m.values())); idx={i:n for n,i in enumerate(ids)}
    cen={c:X[[idx[i] for i in ids if l1m[i]==c]].mean(0) for c in cats}
    amb=[]
    for i in ids:
        x=X[idx[i]]; sims={c:float(x@cen[c]/(np.linalg.norm(x)*np.linalg.norm(cen[c])+1e-12)) for c in cats}
        own=sims[l1m[i]]; other=max((v for c,v in sims.items() if c!=l1m[i]),default=0)
        if other>=thr*own: amb.append(i)
    return amb
ref_l1_alt={}
for i in ids:
    p=[i]
    while p[-1]!=ROOT:
        par=[x for x in T[p[-1]]['is_a'] if x==ROOT or x in desc(ROOT)]; p.append(par[-1])
    ref_l1_alt[i]=p[-2] if len(p)>1 else i
def stats(name,l1m,l2m,other_labels=()):
    sizes=collections.Counter(l1m.values()); s2=collections.Counter(l2m.values())
    oth=sum(1 for i in ids if l2m[i] in other_labels or l1m[i] in other_labels)
    return dict(name=name, terms=N, coverage=100.0, other_pct=round(100*oth/N,1),
        n_L1=len(sizes), n_L2=len(s2), max_L1_share=round(100*max(sizes.values())/N,1),
        mean_L1=round(N/len(sizes),1), singleton_L2=sum(1 for v in s2.values() if v==1),
        mean_L2=round(N/len(s2),1), min_L2=min(s2.values()), max_L2=max(s2.values()),
        ambiguous_09=len(ambiguous(l1m,0.9)), ambiguous_08=len(ambiguous(l1m,0.8)), ambiguous_10=len(ambiguous(l1m,1.0)),
        ARI_L1=round(adjusted_rand_score([ref_l1[i] for i in ids],[l1m[i] for i in ids]),3),
        NMI_L1=round(normalized_mutual_info_score([ref_l1[i] for i in ids],[l1m[i] for i in ids]),3),
        ARI_L1_altparent=round(adjusted_rand_score([ref_l1_alt[i] for i in ids],[l1m[i] for i in ids]),3),
        NMI_L2=round(normalized_mutual_info_score([ref_l2[i] for i in ids],[l2m[i] for i in ids]),3),
        pairF1_L2=round(pair_f1(l2m,ref_l2),3), edge_pres_L1=round(edge_pres(l1m),3))
# глибина/ширина SO (індукована) — для довідки
def depth(i):
    return len(primary_path(i))-1
sodepth=[depth(i) for i in ids]
so_stats=dict(name="SO (еталон, індукована)", terms=N, max_depth=max(sodepth), mean_depth=round(float(np.mean(sodepth)),2),
    n_L1=len(set(ref_l1.values())), n_L2=len(set(ref_l2.values())), multi_parent=len(multi),
    max_children=max(len([c for c in ch[i] if c in desc(ROOT)]) for i in ids+[ROOT]))
S_man=stats("Ручна (зверху вниз)",man_l1,man_l2,other_labels=("Інше",))
S_clu=stats("Кластеризація (знизу вгору)",clu_l1,clu_l2)
S_man.update(max_depth=2, mean_depth=2.0); S_clu.update(max_depth=2, mean_depth=2.0)
# чутливість кластеризації до k1
sens=[]
for k in (4,6,8,10,12,16):
    c=fcluster(Z,k,'maxclust'); m={i:f"C{x}" for i,x in zip(ids,c)}
    sens.append(dict(k=k,ARI=round(adjusted_rand_score([ref_l1[i] for i in ids],[m[i] for i in ids]),3),
        NMI=round(normalized_mutual_info_score([ref_l1[i] for i in ids],[m[i] for i in ids]),3)))
# ---- дефекти
D=[]
# (а) багатобатьківські терміни: втрата is-a
def lost(l1m):
    out=[]
    for i in multi:
        ps=[p for p in T[i]['is_a'] if p in desc(ROOT)]
        groups={l1m[p] for p in ps if p in l1m}
        if len(groups|{l1m[i]})>1: out.append(i)
    return out
lm,lc=lost(man_l1),lost(clu_l1)
# (б) двозначні розміщення в ручній
amb_man=ambiguous(man_l1,0.9)
# (в) структура кластерів
clu_sizes=collections.Counter(clu_l1.values()); clu_info={}
for c in sorted(clu_sizes):
    mem=[i for i in ids if clu_l1[i]==c]; idx=[ids.index(i) for i in mem]
    ref=collections.Counter(ref_l1[i] for i in mem); man=collections.Counter(man_l1[i] for i in mem)
    clu_info[c]=dict(size=len(mem),top_tokens=cname(idx),ref_purity=round(max(ref.values())/len(mem),2),
                     man_purity=round(max(man.values())/len(mem),2),ref_groups=len(ref),members=[T[i]['name'] for i in mem][:6])
# (г) пари з однаковою нормалізованою назвою, розкидані по різних клітинках
def norm(n): return re.sub(r'^five_prime','5_prime',n).replace('three_prime','3_prime')
sib=[]
for a,b in itertools.combinations(ids,2):
    na,nb=norm(T[a]['name']),norm(T[b]['name'])
    if na.replace('_variant','').replace('_location','')==nb.replace('_variant','').replace('_location','') and na!=nb: sib.append((a,b))
# (д) NMD-перехрестя: терміни X_NMD_*, чи вони поруч із базовим X
def base_of(n): return re.sub(r'_NMD_(escaping|triggering)$','',n)
nmd=[i for i in ids if re.search(r'_NMD_(escaping|triggering)$',T[i]['name'])]
nmd_sep_man=sum(1 for i in nmd if man_l2[i]!=man_l2[name2id[base_of(T[i]['name'])]])
nmd_sep_clu=sum(1 for i in nmd if clu_l2[i]!=clu_l2[name2id[base_of(T[i]['name'])]])
nmd_sep_clu1=sum(1 for i in nmd if clu_l1[i]!=clu_l1[name2id[base_of(T[i]['name'])]])
# (ж) родові терміни (предки в межах множини), що стоять у клітинці поруч із видовими / розкидають нащадків
def generic_stats(l1m,l2m):
    cell_pairs=[(T[p]['name'],T[c]['name']) for p,c in edges if p!=ROOT and l2m[p]==l2m[c]]
    anc_multi=[]
    for i in ids:
        dd=[x for x in desc(i) if x in l1m]
        if len({l1m[x] for x in dd}|{l1m[i]})>1 and len(dd)>=3: anc_multi.append((T[i]['name'],len(dd),len({l1m[x] for x in dd})))
    return dict(is_a_pairs_same_L2=len(cell_pairs),is_a_edges_total=len([1 for p,c in edges if p!=ROOT]),examples=cell_pairs[:5],
                generic_spanning=sorted(anc_multi,key=lambda x:-x[1])[:6],n_generic_spanning=len(anc_multi))
gen_man=generic_stats(man_l1,man_l2); gen_clu=generic_stats(clu_l1,clu_l2)
# (е) порівняння дрібного рівня SO: скільки термінів ручна відокремила від SO-брата
out=dict(N=N,k1=k1,k2=k2,linkage={m:dict(silhouette=v['sil'],sizes=v['sizes']) for m,v in LINK.items()},best_linkage=best,so=so_stats,manual=S_man,cluster=S_clu,sensitivity=sens,
  multi_parent_total=len(multi),multi_lost_manual=len(lm),multi_lost_cluster=len(lc),
  amb_manual=[T[i]['name'] for i in amb_man],amb_cluster=[T[i]['name'] for i in ambiguous(clu_l1,0.9)],
  cluster_info=clu_info, ref_L1_sizes={T[k]['name']:v for k,v in collections.Counter(ref_l1.values()).items()},
  manual_L1_sizes=dict(collections.Counter(man_l1.values())), naming_pairs=[(T[a]['name'],T[b]['name'],man_l2[a]==man_l2[b],clu_l2[a]==clu_l2[b]) for a,b in sib],
  generic=dict(manual=gen_man,cluster=gen_clu),
  nmd=dict(n=len(nmd),sep_manual=nmd_sep_man,sep_cluster_L2=nmd_sep_clu,sep_cluster_L1=nmd_sep_clu1))
json.dump(out,open('metrics.json','w'),ensure_ascii=False,indent=1)
# ---- таксономії у єдиному форматі (skos:broader)
def tax_json(label,l1m,l2m,l1name=lambda x:x,l2name=lambda x:x):
    nodes=[dict(id=f"{label}:L1:{a}",label=l1name(a),broader=None) for a in sorted(set(l1m.values()))]
    seen=set()
    for i in ids:
        a,b=l1m[i],l2m[i]
        if b not in seen:
            seen.add(b); nodes.append(dict(id=f"{label}:L2:{b}",label=l2name(b),broader=f"{label}:L1:{a}"))
    for i in ids: nodes.append(dict(id=i,label=T[i]['name'],broader=f"{label}:L2:{l2m[i]}"))
    return dict(scheme=label,nodes=nodes)
c1n={c:cname([ids.index(i) for i in ids if clu_l1[i]==c]) for c in set(clu_l1.values())}
c2n={c:cname([ids.index(i) for i in ids if clu_l2[i]==c]) for c in set(clu_l2.values())}
so_nodes=dict(scheme="SO",nodes=[dict(id=i,label=T[i]['name'],broader=(T[i]['is_a'][0] if T[i]['is_a'][0] in T else None)) for i in ids])
json.dump(dict(manual=tax_json("manual",man_l1,man_l2),cluster=tax_json("cluster",clu_l1,clu_l2,lambda c:f"{c} [{c1n[c]}]",lambda c:f"{c} [{c2n[c]}]"),
  reference_SO=so_nodes),open('taxonomies.json','w'),ensure_ascii=False,indent=1)
# ---- таблиця термінів
rows=[(i,T[i]['name'],T[i].get('def','')[:200],T[ref_l1[i]]['name'] if ref_l1[i]!=i else T[i]['name'],T[ref_l2[i]]['name'] if ref_l2[i] in T else '',
       man_l1[i],man_l2[i],f"{clu_l1[i]} [{c1n[clu_l1[i]]}]",f"{clu_l2[i]} [{c2n[clu_l2[i]]}]",len([x for x in T[i]['is_a'] if x in desc(ROOT) or x==ROOT])>1) for i in ids]
json.dump(rows,open('terms_table.json','w'),ensure_ascii=False)
print(json.dumps({k:out[k] for k in ('linkage','best_linkage','k1','k2','so','manual','cluster','sensitivity','multi_parent_total','multi_lost_manual','multi_lost_cluster','nmd','ref_L1_sizes')},ensure_ascii=False,indent=1))
print('amb_manual',out['amb_manual']); print('amb_cluster',out['amb_cluster'])
for c,v in clu_info.items(): print(c,v)
print(out['naming_pairs']); print(json.dumps(out['generic'],ensure_ascii=False,indent=1))
