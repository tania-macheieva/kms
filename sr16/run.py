import argparse,json,time
from pathlib import Path
import pandas as pd,numpy as np,scipy.sparse as sp
from scipy.sparse.linalg import svds
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser()
ap.add_argument('--ratings',type=Path,default=ROOT/'data'/'ratings.dat')
ap.add_argument('--movies',type=Path,default=ROOT/'data'/'movies.dat')
ap.add_argument('--out',type=Path,default=ROOT/'results.json')
args=ap.parse_args()
for path in (args.ratings,args.movies):
    if not path.is_file():
        raise FileNotFoundError(f'Вхідний файл не знайдено: {path}. Передайте --ratings і --movies.')
rng=np.random.default_rng(16); np.random.seed(16)
r=pd.read_csv(args.ratings,sep='::',engine='python',names=['u','i','r','t']); r['i']=r['i'].astype(str).str.zfill(7)
m=pd.read_csv(args.movies,sep='::',engine='python',names=['i','title','g'],dtype={'i':str})
m['y']=m.title.str.extract(r'\((\d{4})\)\s*$')[0].astype(float)
T=r.t.quantile(.8)
pool=m[m.y<=2018].reset_index(drop=True); iid={x:k for k,x in enumerate(pool.i)}; NI=len(pool)
r['ix']=r.i.map(iid); n_all_test_pos=((r.t>=T)&(r.r>=8)).sum()
r=r[r.ix.notna()].copy(); r['ix']=r.ix.astype(int)
excl_share=1-((r.t>=T)&(r.r>=8)).sum()/n_all_test_pos
tr=r[r.t<T]; te=r[r.t>=T]
users=pd.Index(sorted(r.u.unique())); uix={u:k for k,u in enumerate(users)}
def mat(df): return sp.csr_matrix((np.ones(len(df),dtype=np.float32),(df.u.map(uix).values,df.ix.values)),shape=(len(users),NI))
Rall=mat(tr); Rall.data[:]=1               # seen (any rating)
trp=tr[tr.r>=8]; Rpos=mat(trp); Rpos.data[:]=1  # positives
pop=np.asarray(Rpos.sum(0)).ravel(); NU=(np.asarray(Rpos.sum(1)).ravel()>0).sum()
seen_item=np.asarray(Rall.sum(0)).ravel()>0; cold_item=~seen_item
# --- models: all take binary profile X (batch x NI sparse) -> scores
k=64; deg=np.asarray(Rpos.sum(1)).ravel()
t0=time.time(); U_,S_,Vt=svds(Rpos.astype(np.float32),k=k); V=Vt.T.astype(np.float32); print('svd',time.time()-t0)
# content features
genres=sorted({g for s in pool.g.dropna() for g in s.split('|')}); gi={g:j for j,g in enumerate(genres)}
dec=sorted({int(y//10*10) for y in pool.y}); 
F=np.zeros((NI,len(genres)+len(dec)),dtype=np.float32)
for a,(g,y) in enumerate(zip(pool.g,pool.y)):
    if isinstance(g,str):
        for x in g.split('|'): F[a,gi[x]]=1
    F[a,len(genres)+dec.index(int(y//10*10))]=1
idf=np.log((NI+1)/(F.sum(0)+1))+1; F=F*idf; F/=np.maximum(np.linalg.norm(F,axis=1,keepdims=True),1e-9)
Fg=(F[:,:len(genres)]>0).astype(np.float32)
Pui=sp.diags(1/np.maximum(np.asarray(Rpos.sum(1)).ravel(),1))@Rpos      # users->items
Piu=sp.diags(1/np.maximum(pop,1))@Rpos.T                                 # items->users
def s_pop(X): return np.tile(np.log1p(pop).astype(np.float32),(X.shape[0],1))
def s_content(X):
    n=np.asarray(X.sum(1)).ravel(); P=X@F; P/=np.maximum(np.linalg.norm(P,axis=1,keepdims=True),1e-9); return (P@F.T).astype(np.float32)
def s_svd(X): return ((X@V)@V.T).astype(np.float32)
def s_p3(X):
    X=sp.diags(1/np.maximum(np.asarray(X.sum(1)).ravel(),1))@X
    return np.asarray((X@Piu@Pui).todense(),dtype=np.float32)
def z(S):
    return (S-S.mean(1,keepdims=True))/np.maximum(S.std(1,keepdims=True),1e-9)
def s_hyb(X):
    n=np.asarray(X.sum(1)).ravel(); S=z(s_svd(X))+z(s_content(X))+z(s_pop(X)+1e-6*np.random.rand(X.shape[0],NI).astype(np.float32))
    S[n==0]=z(s_pop(X[n==0]))*3 if (n==0).any() else S[n==0]; return S
def s_rand(X): return np.random.default_rng(5).random((X.shape[0],NI),dtype=np.float32)
def s_pen(lam): 
    def f(X): return z(s_svd(X))-lam*z(s_pop(X))
    return f
MODELS={'Популярність':s_pop,'Content-based (жанр+десятиліття)':s_content,'Embedding (SVD, k=64)':s_svd,'Граф (P3, random walk)':s_p3,'Гібрид (SVD+content+pop)':s_hyb,'Random':s_rand}
# --- eval users
tep=te[te.r>=8]
def truth_sets(df,seen=None):
    return {u:set(items) for u,items in df.groupby('u')['ix']}
trainseen_by_u={}
Rall_csr=Rall.tocsr()
trpos_n=np.asarray(Rpos.sum(1)).ravel()
tt=truth_sets(tep)
warm=[u for u in tt if trpos_n[uix[u]]>=3]
warm_truth={}
for u in warm:
    s=set(tt[u])-set(Rall_csr[uix[u]].indices)
    if s: warm_truth[u]=s
warm=sorted(warm_truth); warm=list(rng.choice(warm,size=min(6000,len(warm)),replace=False))
print('warm users',len(warm_truth),'->',len(warm))
LOG=np.log2(np.arange(2,12))
def evaluate(score_fn,uids,truths,Xfun,cand_mask=None,batch=400,keep_lists=True):
    P5=[];ND=[];HR=[];lists=[]
    for b in range(0,len(uids),batch):
        U=uids[b:b+batch]; X=Xfun(U); S=score_fn(X).copy()
        for a,u in enumerate(U):
            S[a,Rall_csr[uix[u]].indices]=-1e9 if not hasattr(Xfun,'noseen') else S[a,0]
        if cand_mask is not None: S[:,~cand_mask]=-1e9
        top=np.argpartition(-S,10,axis=1)[:,:10]
        for a,u in enumerate(U):
            o=top[a][np.argsort(-S[a,top[a]])]; lists.append(o); t=truths[u]
            hit=np.array([x in t for x in o],dtype=float)
            P5.append(hit[:5].mean()); HR.append(hit.max()); 
            idcg=LOG[:min(len(t),10)]; ND.append((hit/LOG).sum()/ (1/idcg).sum())
    return np.array(P5),np.array(ND),np.array(HR),np.array(lists)
def Xwarm(U): return Rpos[[uix[u] for u in U]]
def catalog_metrics(L):
    flat=L.ravel(); cov=len(set(flat))/NI
    nov=float(np.mean(-np.log2((pop[flat]+1)/(NU+1))))
    c=np.bincount(flat,minlength=NI).astype(float); c.sort(); n=len(c); g=(2*np.arange(1,n+1)-n-1).dot(c)/(n*c.sum())
    top1=np.sort(np.bincount(flat,minlength=NI))[::-1][:max(1,int(.01*NI))].sum()/len(flat)
    ild=[]
    for l in L[::5]:
        G=Fg[l]; nrm=np.maximum(np.linalg.norm(G,axis=1,keepdims=True),1e-9); C=(G/nrm)@(G/nrm).T; ild.append(1-(C.sum()-10)/90)
    return dict(coverage=cov,novelty=nov,gini=float(g),top1pct_share=float(top1),ild=float(np.mean(ild)))
def ci(x,B=1000):
    rr=np.random.default_rng(1); bs=[x[rr.integers(0,len(x),len(x))].mean() for _ in range(B)]; return float(np.percentile(bs,2.5)),float(np.percentile(bs,97.5))
res={'meta':dict(T=str(pd.to_datetime(T,unit='s')),n_train=len(tr),n_test=len(te),pool=NI,excluded_test_pos_share=float(excl_share),train_users=int(NU),warm_users_total=len(warm_truth),warm_eval=len(warm),k=k,cold_items_in_pool=int(cold_item.sum()),genres=len(genres))}
main={}; per_user={}
for name,f in MODELS.items():
    t0=time.time(); p5,nd,hr,L=evaluate(f,warm,warm_truth,Xwarm); met=catalog_metrics(L)
    main[name]=dict(P5=float(p5.mean()),P5_ci=ci(p5),nDCG10=float(nd.mean()),nDCG_ci=ci(nd),HR10=float(hr.mean()),**met,sec=time.time()-t0)
    per_user[name]=(p5,nd); print(name,{k_:round(v,4) if isinstance(v,float) else v for k_,v in main[name].items()})
res['main']=main
res['paired']={}
for a,b in [('Embedding (SVD, k=64)','Популярність'),('Граф (P3, random walk)','Популярність'),('Embedding (SVD, k=64)','Граф (P3, random walk)'),('Content-based (жанр+десятиліття)','Популярність')]:
    d=per_user[a][0]-per_user[b][0]; dn=per_user[a][1]-per_user[b][1]; res['paired'][a+' - '+b]=dict(P5=float(d.mean()),P5_ci=ci(d),nDCG=float(dn.mean()),nDCG_ci=ci(dn))
print(res['paired'])
# --- random split (for the "why not random" demo): same test users' interactions, random 80/20 over all positive ratings
rs=r[r.r>=8].sample(frac=1,random_state=3); cut=int(.8*len(rs)); rtr,rte=rs.iloc[:cut],rs.iloc[cut:]
Rr=mat(rtr); Rr.data[:]=1; rpop=np.asarray(Rr.sum(0)).ravel()
tr_t=rte.groupby('u').ix.apply(set).to_dict()
ru=[u for u in tr_t if Rr[uix[u]].nnz>=3]; ru=list(rng.choice(ru,size=min(6000,len(ru)),replace=False))
rt={u:set(tr_t[u])-set(Rr[uix[u]].indices) for u in ru}; ru=[u for u in ru if rt[u]]
Rall_backup=Rall_csr; Rall_csr=Rr.tocsr()
pop_b=pop; pop=rpop
rand_res={}
for name,f in [('Популярність',s_pop)]:
    p5,nd,hr,L=evaluate(f,ru,rt,lambda U:Rr[[uix[u] for u in U]]); rand_res[name]=dict(P5=float(p5.mean()),nDCG10=float(nd.mean()))
# SVD on random split
U2,S2,Vt2=svds(Rr.astype(np.float32),k=k); V_b=V; V=Vt2.T.astype(np.float32)
p5,nd,hr,L=evaluate(s_svd,ru,rt,lambda U:Rr[[uix[u] for u in U]]); rand_res['Embedding (SVD, k=64)']=dict(P5=float(p5.mean()),nDCG10=float(nd.mean()))
V=V_b; pop=pop_b; Rall_csr=Rall_backup
res['random_split']=rand_res; print('random split',rand_res)
# --- cold start: users with no train ratings
first_seen=tr.groupby('u').size()
TRU=set(tr.u); cold_u=[u for u in tep.u.unique() if u not in TRU]; COLD=set(cold_u)
cs={}
tes=te.sort_values(['u','t'])
pos_lists={u:list(g[g.r>=8].ix) for u,g in tes.groupby('u') if u in COLD}
cu=[u for u,l in pos_lists.items() if len(dict.fromkeys(l))>=7]
cu=list(rng.choice(sorted(cu),size=min(3000,len(cu)),replace=False)); print('cold users',len(cu),'of',len(cold_u))
first5={u:list(dict.fromkeys(pos_lists[u]))[:5] for u in cu}; ctruth={u:set(dict.fromkeys(pos_lists[u]))-set(first5[u]) for u in cu}
res['meta']['cold_users_total']=len(cold_u); res['meta']['cold_users_eval']=len(cu)
Rall_csr=sp.csr_matrix((len(users),NI),dtype=np.float32).tolil()
for u in cu:
    Rall_csr[uix[u],first5[u]]=1
Rall_csr=Rall_csr.tocsr()
for n in [0,1,2,3,5]:
    def Xc(U,n=n):
        rows=[];cols=[]
        for a,u in enumerate(U):
            for c in first5[u][:n]: rows.append(a);cols.append(c)
        return sp.csr_matrix((np.ones(len(rows),dtype=np.float32),(rows,cols)),shape=(len(U),NI))
    for name in ['Популярність','Content-based (жанр+десятиліття)','Embedding (SVD, k=64)','Граф (P3, random walk)','Гібрид (SVD+content+pop)']:
        f=MODELS[name]
        if n==0 and name!='Популярність' and name!='Гібрид (SVD+content+pop)':
            f=s_pop      # fallback: no profile -> popularity
        p5,nd,hr,L=evaluate(f,cu,ctruth,Xc); cs.setdefault(name,{})[n]=dict(P5=float(p5.mean()),nDCG10=float(nd.mean()),P5_ci=ci(p5),coverage=len(set(L.ravel()))/NI)
    print('cold n',n,{k_:round(v[n]['P5'],4) for k_,v in cs.items()})
res['cold_users']=cs
# --- cold items among warm users
Rall_csr=Rall_backup
cm=cold_item
ct={}
for u in warm:
    s=set(warm_truth[u])&set(np.where(cm)[0])
    if s: ct[u]=s
cwu=list(ct); print('warm users with a cold-item positive',len(cwu))
tot_pos=sum(len(v) for v in warm_truth.values()); cold_pos=sum(len(v) for v in ct.values())
res['cold_items']=dict(share_of_test_positives=cold_pos/tot_pos,users=len(cwu),n_cold_items=int(cm.sum()))
for name,f in MODELS.items():
    p5,nd,hr,L=evaluate(f,cwu,ct,Xwarm,cand_mask=cm)
    res['cold_items'][name]=dict(P5=float(p5.mean()),nDCG10=float(nd.mean()),HR10=float(hr.mean()))
print(res['cold_items'])
# --- mitigation: popularity penalty
mit={}
for lam in [0,1.5,3,5,8,12]:
    p5,nd,hr,L=evaluate(s_pen(lam),warm,warm_truth,Xwarm); mit[lam]=dict(P5=float(p5.mean()),nDCG10=float(nd.mean()),**catalog_metrics(L)); print('lam',lam,{k_:round(v,4) for k_,v in mit[lam].items()})
res['mitigation']=mit
args.out.parent.mkdir(parents=True,exist_ok=True)
args.out.write_text(json.dumps(res,ensure_ascii=False,indent=1,default=float),encoding='utf-8')
