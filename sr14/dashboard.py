import json,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
s1=json.load(open('snap/s1.json')); s2=json.load(open('snap/s2.json')); th=json.load(open('thresholds.json')); f=json.load(open('snap/s1_asof_1116.json'))
fig,ax=plt.subplots(1,2,figsize=(9.2,2.7),dpi=200,gridspec_kw={'width_ratios':[1.25,1]})
names=['M1 повнота','M2 точність','M3 унікальність','M4 узгодженість','M5 актуальність']; keys=['M1','M2','M3','M4','M5']
y=list(range(len(keys)))[::-1]
for yy,k in zip(y,keys):
    a,b=s1['metrics'][k],s2['metrics'][k]
    ax[0].plot([a,b],[yy,yy],color='#9aa5b1',lw=2,zorder=1)
    ax[0].scatter(a,yy,color='#d95f02',s=34,zorder=3,label='S1: до очищення' if yy==y[0] else None)
    ax[0].scatter(b,yy,color='#1b6ca8',s=34,zorder=3,label='S2: після очищення' if yy==y[0] else None)
    ax[0].plot([th['chat'][k]]*2,[yy-.28,yy+.28],color='#1b9e77',lw=1.6,label='поріг «чат»' if yy==y[0] else None)
    ax[0].plot([th['audit'][k]]*2,[yy-.28,yy+.28],color='#7b3294',lw=1.6,ls=':',label='поріг «аудит»' if yy==y[0] else None)
fm=f['metrics']['M5']; ax[0].scatter(fm,y[-1],marker='x',color='#d62728',s=40,zorder=4,label='M5 на 16.11 (без змін)')
ax[0].set_yticks(y); ax[0].set_yticklabels(names,fontsize=7.5); ax[0].set_xlim(0.48,1.012); ax[0].tick_params(axis='x',labelsize=7)
ax[0].set_title('Корпус: 2 заміри (12.11.2026) і прогноз актуальності',fontsize=8.3); ax[0].legend(fontsize=6,frameon=False,loc='lower left',bbox_to_anchor=(0,-.02))
runs=s1['runs']; lab=[f"{k}\n{v['date'][5:]}" for k,v in runs.items()]
for key,c,nm in [('faithfulness','#1b6ca8','M6 вірність'),('context_recall','#d95f02','M7 повнота контексту')]:
    ax[1].plot(lab,[v[key] for v in runs.values()],marker='o',color=c,lw=1.6,label=nm)
for key,c in [('M6','#1b6ca8'),('M7','#d95f02')]:
    ax[1].axhline(th['chat'][key],color=c,lw=.8,ls='--'); ax[1].axhline(th['audit'][key],color=c,lw=.8,ls=':')
ax[1].set_ylim(.80,1.01); ax[1].tick_params(labelsize=7); ax[1].legend(fontsize=6.5,frameon=False,loc='lower left')
ax[1].set_title('Тренд за прогонами (пунктир — «чат», крапки — «аудит»)',fontsize=8.3)
for a in ax:
    for s in ['top','right']: a.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig('dashboard.png')
