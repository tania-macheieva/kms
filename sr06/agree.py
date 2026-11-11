import json, itertools, numpy as np
from scipy.stats import spearmanr, pearsonr
from sklearn.metrics import cohen_kappa_score
L=json.load(open('letters.json'))
K=['K1','K2','K3','K4','K5']
raw={'R1':json.load(open('R1_raw.json')),'R2':json.load(open('R2_raw.json'))}
S={}  # S[rater][map]=[5]
for r in raw:
    S[r]={L[r][let]:[raw[r][let][k] for k in K] for let in 'ABC'}
json.dump(S,open('scores_blind.json','w'),indent=1)
maps=['expert','llm','peer']
a=[S['R1'][m][i] for m in maps for i in range(5)]; b=[S['R2'][m][i] for m in maps for i in range(5)]
d=np.abs(np.array(a)-np.array(b))
res=dict(n_pairs=len(a),mean_abs_diff=round(float(d.mean()),3),exact=round(float((d==0).mean()),3),within1=round(float((d<=1).mean()),3),
 pearson=round(float(pearsonr(a,b)[0]),3),spearman=round(float(spearmanr(a,b)[0]),3),
 kappa_quadratic=round(float(cohen_kappa_score(a,b,weights='quadratic',labels=[0,1,2])),3),
 kappa_plain=round(float(cohen_kappa_score(a,b,labels=[0,1,2])),3),
 by_crit={k:round(float(np.mean([abs(S['R1'][m][i]-S['R2'][m][i]) for m in maps])),2) for i,k in enumerate(K)},
 by_map={m:round(float(np.mean([abs(S['R1'][m][i]-S['R2'][m][i]) for i in range(5)])),2) for m in maps},
 totals={r:{m:sum(S[r][m]) for m in maps} for r in S},
 total_diff={m:sum(S['R1'][m])-sum(S['R2'][m]) for m in maps},
 biggest=[(m,K[i],S['R1'][m][i],S['R2'][m][i]) for m in maps for i in range(5) if abs(S['R1'][m][i]-S['R2'][m][i])==d.max()],
 rank={r:sorted(maps,key=lambda m:-sum(S[r][m])) for r in S},
 total_corr_note="n=3 карти: кореляція сум неінформативна")
json.dump(res,open('agreement.json','w'),ensure_ascii=False,indent=1); print(json.dumps(res,ensure_ascii=False,indent=1))
