import json,matplotlib
from pathlib import Path
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
with open(ROOT/'results.json',encoding='utf-8') as f: r=json.load(f)
C={'Популярність':'#7f7f7f','Content-based (жанр+десятиліття)':'#d95f02','Embedding (SVD, k=64)':'#1b6ca8','Граф (P3, random walk)':'#1b9e77','Гібрид (SVD+content+pop)':'#7b3294'}
short={'Популярність':'Popularity','Content-based (жанр+десятиліття)':'Content','Embedding (SVD, k=64)':'SVD embedding','Граф (P3, random walk)':'Graph P3','Гібрид (SVD+content+pop)':'Hybrid'}
fig,ax=plt.subplots(1,2,figsize=(9,3.1),dpi=200)
ns=[0,1,2,3,5]
for k,c in C.items():
    y=[r['cold_users'][k][str(n)]['P5'] for n in ns]
    ax[0].plot(ns,y,marker='o',ms=3.5,lw=1.6,color=c,label=short[k],ls='--' if k=='Популярність' else '-')
ax[0].set_xlabel('кількість відомих лайків нового користувача (n)',fontsize=8); ax[0].set_ylabel('Precision@5',fontsize=8)
ax[0].set_title('Холодний старт користувача (1230 нових користувачів)',fontsize=8.5); ax[0].legend(fontsize=7,frameon=False,loc='center right',bbox_to_anchor=(1,0.45)); ax[0].tick_params(labelsize=7); ax[0].set_xticks(ns)
for s in ['top','right']: ax[0].spines[s].set_visible(False); ax[1].spines[s].set_visible(False)
for k,c in C.items():
    v=r['main'][k]; ax[1].scatter(v['coverage']*100,v['P5'],color=c,s=28,zorder=3)
    ax[1].annotate(short[k],(v['coverage']*100,v['P5']),fontsize=6.5,xytext=(3,3),textcoords='offset points')
lam=[0,1.5,3,5,8]; xs=[r['mitigation'][str(l) if str(l) in r['mitigation'] else str(float(l))]['coverage']*100 for l in lam]; ys=[r['mitigation'][str(l) if str(l) in r['mitigation'] else str(float(l))]['P5'] for l in lam]
ax[1].plot(xs,ys,color='#1b6ca8',lw=1,ls=':',zorder=2)
for l,x,y in zip(lam,xs,ys): ax[1].annotate(f'λ={l}',(x,y),fontsize=6.5,color='#1b6ca8',xytext=(3,-8),textcoords='offset points')
ax[1].set_xlabel('Coverage@10, % каталогу',fontsize=8); ax[1].set_ylabel('Precision@5',fontsize=8)
ax[1].set_title('Точність vs покриття; пунктир — SVD зі штрафом за популярність',fontsize=8.5); ax[1].tick_params(labelsize=7)
plt.tight_layout(); plt.savefig(ROOT/'charts.png')
