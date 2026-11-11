#!/usr/bin/env python3
"""СР6: метрики карт, виправлення LLM-карти, каталог помилок. Вхід: lab06_repo (моделі), вихід: JSON/xlsx/png."""
import json, collections, copy
from pathlib import Path
B=str(Path(__file__).resolve().parent) + '/'
CL={}  # label -> cluster (G геноміка/дані, Q якість, C клініка)
for fn in ('cmap_expert','cmap_peer'):
    for c in json.load(open(B+f'models/{fn}.json'))['concepts']: CL.setdefault(c['label'],c['cluster'])
def cl(label):
    if label in CL: return CL[label]
    if any(ch in label for ch in '<>'): return 'Q'
    return None
# ---------- завантаження карт у єдиний формат: nodes{label:kind}, edges[...]
def load(fn,pref):
    m=json.load(open(B+f'models/{fn}.json')); lab={c['id']:c['label'] for c in m['concepts']}; kind={c['label']:c['kind'] for c in m['concepts']}
    E=[dict(id=q['id'],s=lab[q['s']],p=q['p'],o=lab[q['o']],cross=q.get('cross',False),expl=q.get('explanation','')) for q in m['propositions']]
    return dict(nodes=kind,edges=E)
def load_llm():
    tr=[json.loads(l) for l in open(B+'models/triples_llm.jsonl')]; nodes={}
    for t in tr:
        for x in (t['s'],t['o']): nodes[x]='instance' if any(ch in x for ch in '<>') else 'concept'
    return dict(nodes=nodes,edges=[dict(id=t['id'],s=t['s'],p=t['p'],o=t['o'],cross=False,expl='',evidence=t['evidence'],source=t['source']) for t in tr])
MAPS={'expert':load('cmap_expert','P'),'llm':load_llm(),'peer':load('cmap_peer','Q')}
# ---------- метрики
def metrics(M):
    nodes,E=M['nodes'],M['edges']
    inst=[n for n,k in nodes.items() if k!='concept']
    rel=collections.Counter(e['p'] for e in E)
    # ієрархія: загальне -> часткове
    g=collections.defaultdict(set)
    for e in E:
        if e['p'] in('is_a','part_of'): g[e['o']].add(e['s'])
        elif e['p']=='has_example': g[e['s']].add(e['o'])
    memo={}
    def depth(n,stack=()):
        if n in memo: return memo[n]
        if n in stack: return 1
        d=1+max((depth(c,stack+(n,)) for c in g[n]),default=0); memo[n]=d; return d
    children={c for v in g.values() for c in v}; roots=[n for n in g if n not in children]
    dmax=max((depth(r) for r in roots),default=1)
    bridges=[e for e in E if cl(e['s']) and cl(e['o']) and cl(e['s'])!=cl(e['o'])]
    # зв'язність
    adj=collections.defaultdict(set)
    for e in E: adj[e['s']].add(e['o']); adj[e['o']].add(e['s'])
    seen=set(); comps=0
    for n in nodes:
        if n in seen: continue
        comps+=1; st=[n]
        while st:
            x=st.pop()
            if x in seen: continue
            seen.add(x); st.extend(adj[x]-seen)
    return dict(concepts=len(nodes)-len(inst),instances=len(inst),propositions=len(E),related_to_pct=round(100*rel.get('related_to',0)/len(E),1),
        relation_types=len(rel),max_hierarchy_levels=dmax,bridging_props=len(bridges),
        bridging_explained=sum(1 for e in bridges if e.get('expl')),components=comps,
        has_annotation_uses_input_pct=round(100*(rel.get('has_annotation',0)+rel.get('uses_input',0))/len(E),1),relations=dict(rel))
# ---------- аудит помилок (ручний, за джерелами sources/*.txt; id -> (клас, серйозність 1-3, примітка))
CAT={
 'E0':'Порогове значення як літерал / без контексту (SNP vs INDEL)',
 'E1':'Змішування сутностей: ген замість варіанта; хвороба замість пацієнтів',
 'E2':'Хибне/неточне відношення або порушення domain/range',
 'E3':'Надмірне узагальнення, категорна помилка',
 'E4':'Тривіальне або надлишкове ребро',
 'E5':'Втрата квантора, умови чи повноти («деякі», «лише для SNP», лише один рак)',
 'E6':'Відсутні крос-зв\'язки / ізольовані гілки',
 'E7':'Слабка підстава (цитата не підтримує твердження)',
 'E8':'Сумнівний напрямок / мета подана як адресат',
 'E9':'Твердження поза джерелами (правдоподібне, але не перевірене)'}
AUD_LLM={
 'L007':('E0',1,'«QD < 2» — літерал без вказання типу варіанта/екземплярного статусу'),
 'L016':('E0',1,'«SOR > 3» — літерал'),'L017':('E0',1,'«MQ < 40» — літерал'),
 'L018':('E0',2,'«FS > 60» без «для SNP»: для INDEL поріг 200 (gatk, коментар) — втрата контексту'),
 'L033':('E1',2,'cascade testing detects BRCA1 — шукають варіант у гені, а не ген'),'L034':('E1',2,'те саме для BRCA2'),
 'L038':('E1',2,'genetic testing detects BRCA1 — має бути pathogenic variant'),'L039':('E1',2,'те саме для BRCA2'),
 'L036':('E5',2,'recommended_for breast cancer: джерело — «для деяких жінок/чоловіків із раком», більшість раків не спадкові'),
 'L037':('E5',1,'аналогічно для ovarian cancer: квантор «деякі» втрачено; об’єкт — захворювання, а не пацієнти'),
 'L011':('E2',2,'rank sum test applies_to allele: тест порівнює якості мапування ридів; allele — лише умова (дубль L010)'),
 'L041':('E2',2,'genetic counseling produces risk assessment: порушує range produces; у джерелі консультант «допомагає з оцінками ризику»'),
 'L030':('E3',3,'genetic variant increases_risk_of hereditary cancer: ризик підвищує лише патогенний варіант'),
 'L015':('E4',1,'VQSR requires genetic variant — тривіально; джерело: потрібні велика кількість варіантів і ресурси відомих варіантів'),
 'L020':('E7',1,'evidence — лише заголовок статті'),'L012':('E7',1,'evidence описує GenotypeGVCFs, а не виклик варіантів загалом (прийнятно, але слабко)'),
}
AUD_PEER={
 'Q06':('E2',1,'genetic variant has_annotation rank sum test: тест — не показник варіанта (мав би бути MQRankSum/ReadPosRankSum)'),
 'Q29':('E5',2,'genetic testing recommended_for breast cancer: квантор «деякі» втрачено'),'Q30':('E5',1,'те саме для ovarian cancer'),
 'Q47':('E4',1,'data quality applies_to VCF file — розпливчасте, без пояснення'),
 'Q48':('E8',1,'variant filtering recommended_for data quality: мета подана як адресат рекомендації'),
 'Q41':('E9',1,'genetic counseling recommended_for cascade testing: у джерелі консультант лише допомагає вирішити, чи тестувати'),
 'Q42':('E9',1,'cascade testing requires informed consent: у джерелі лише «ті, хто вирішать пройти тест»'),
 'Q44':('E9',1,'risk assessment uses_input autosomal dominant inheritance: відсутнє в джерелах'),
 'Q21':('E9',1,'BRCA1 part_of gene panel: у CDC-джерелі панелей немає (GATK згадує малі панелі загалом)'),'Q22':('E9',1,'те саме для BRCA2'),
 'Q52':('E9',2,'genetic testing uses_input VCF file: крос-зв\'язок спирається на припущення, що клінічний тест споживає відфільтрований VCF; у джерелах цього немає'),
}
def sig(M,s,p,o):
    for e in M['edges']:
        if (e['s'],e['p'],e['o'])==(s,p,o): return e['id']
AUD_EXP={}
EX=MAPS['expert']
for (s,p,o),v in {('breast cancer','is_a','hereditary cancer'):('E3',2,'не кожен рак молочної залози спадковий (CDC): is_a перебільшує'),
 ('ovarian cancer','is_a','hereditary cancer'):('E3',2,'те саме для рака яєчників'),
 ('BRCA1','increases_risk_of','breast cancer'):('E5',1,'CDC називає обидва гени для обох раків; пропущено BRCA1→ovarian'),
 ('BRCA2','increases_risk_of','ovarian cancer'):('E5',1,'пропущено BRCA2→breast'),
 ('strand odds ratio','recommended_for','exon'):('E2',2,'не пояснює, що FS штрафує кінці екзонів і тому перевіряють SOR'),
 ('variant quality score recalibration','requires','genetic variant'):('E4',1,'тривіально; джерело: велика кількість варіантів і ресурси відомих варіантів')}.items():
    AUD_EXP[sig(EX,s,p,o)]=v
assert None not in AUD_EXP
# ---------- виправлення LLM-карти
FIX=[]  # (id, клас, що змінено, чому, джерело/статус)
def build_fixed():
    M=copy.deepcopy(MAPS['llm']); E=M['edges']; N=M['nodes']; by={e['id']:e for e in E}
    rm=set(); new=[]
    def add(s,p,o,fix,cross=False,expl='',status='verified',src='',qual='',kind=None):
        for x in (s,o):
            if x not in N: N[x]=kind.get(x,'concept') if kind else 'concept'
        new.append(dict(id=f"N{len(new)+1:02d}",s=s,p=p,o=o,cross=cross,expl=expl,fix=fix,status=status,source=src,qualifier=qual))
    def mark(i,fix): by[i]['fix']=fix
    # F01 gene/variant
    for i in ('L032','L033','L034','L038','L039'): rm.add(i); mark(i,'F01')
    add('cascade testing','detects','pathogenic variant','F01',src='cdc: «checked for the same genetic change that you have»')
    add('genetic testing','detects','pathogenic variant','F01',cross=True,expl='Клінічний тест шукає в ДНК той самий тип патогенних варіантів, які у геномному конвеєрі проходять фільтрацію якості; саме це поєднує дві частини фокусного питання.',src='cdc: «Genetic testing for BRCA1, BRCA2, and other genetic changes»')
    # F02 rank-sum
    rm.add('L011'); mark('L011','F02')
    # F03 counseling produces risk assessment
    rm.add('L041'); mark('L041','F03')
    add('risk assessment','applies_to','relative','F03',src='cdc: «personalized risk estimates for each person in your family»')
    # F04 over-generalisation
    rm.add('L030'); mark('L030','F04')
    add('pathogenic variant','increases_risk_of','hereditary cancer','F04',cross=True,expl='Лише патогенний варіант (BRCA1/BRCA2) підвищує ризик спадкового раку; цей зв\'язок переводить результат геномної фільтрації в клінічний ризик.',src='cdc L029–L030',)
    add('pathogenic variant','is_a','genetic variant','F04',status='expert_asserted',src='таксономія ЛР5')
    add('BRCA1','is_a','gene','F04',status='expert_asserted',src='таксономія ЛР5'); add('BRCA2','is_a','gene','F04',status='expert_asserted',src='таксономія ЛР5')
    # F05 VQSR trivial
    rm.add('L015'); mark('L015','F05')
    add('variant quality score recalibration','requires','large set of variants','F05',src='gatk: «requires a large number of variants»')
    add('variant quality score recalibration','requires','known variant resources','F05',src='gatk: «well-curated known variant resources»')
    # F06 quantifier
    for i in ('L036','L037'): by[i]['qualifier']='для деяких пацієнтів'; mark(i,'F06')
    # F07 thresholds
    for i in ('L007','L016','L017'): mark(i,'F07')
    by['L018']['o']='FS > 60 (SNP)'; N.pop('FS > 60',None); N['FS > 60 (SNP)']='instance'; mark('L018','F07')
    for s,p,o,sr in (('Fisher strand bias','has_example','FS > 200 (INDEL)','gatk (коментар): FS >60 SNP / >200 INDEL'),
                     ('rank sum test','has_example','MQRankSum < −12,5','gatk: «none of your variants have MQRankSum less than -12.5»'),
                     ('rank sum test','has_example','ReadPosRankSum < −8','gatk: L019')):
        add(s,p,o,'F07',src=sr,kind={o:'instance'})
    # F08 weak evidence
    by['L020']['evidence']='generic hard-filtering recommendations that we provide as a substitute for VQSR (the method we normally recommend for filtering germline short variants)'; mark('L020','F08')
    # F09 relatives hierarchy
    for deg,ex,pct in (('first-degree relative','батьки, діти, рідні брати/сестри: 50 %',''),('second-degree relative','зведені брати/сестри, тітки/дядьки, бабусі/дідусі: 25 %',''),('third-degree relative','двоюрідні та далі: до 12,5 %','')):
        add(deg,'is_a','relative','F09',status='expert_asserted',src='таксономія ЛР5; cdc: відсотки за ступенями')
        add(deg,'has_example',ex,'F09',src='cdc: «1 in 2 (50%)», «1 in 4 (25%)», «as much as a 1 in 8 (12.5%)»',kind={ex:'instance'})
    add('cascade testing','recommended_for','first-degree relative','F09',cross=True,expl='Ймовірність носійства визначає чергу тестування: спершу найближчі родичі (50 %), далі віддаленіші, якщо найближчі недоступні.',src='cdc: «testing should start with family members who are most closely related»')
    add('cascade testing','requires','age ≥ 18 (виняток: дитячий ризик)','F09',src='cdc: «18 years of age and older»',kind={'age ≥ 18 (виняток: дитячий ризик)':'instance'})
    # F10 cross-links
    add('hard filtering','recommended_for','gene panel','F10',cross=True,expl='Для малих генних панелей (до яких належать BRCA1/BRCA2) VQSR неможливий через малу кількість варіантів, тому доводиться застосовувати жорстку фільтрацію.',src='gatk: «For those of you working with small gene panels … you have to fall back on hard-filtering»')
    add('cascade testing','requires','pathogenic variant','F10',cross=True,expl='Каскадне тестування шукає в родичів той самий варіант, що знайдено в пробанда; без підтвердженого патогенного варіанта його не запустити — отже, якість фільтрації впливає на клінічне рішення.',src='cdc: «checked for the same genetic change that you have»')
    for i in rm: pass
    for k,v in list(N.items()): pass
    edges=[e for e in E if e['id'] not in rm]+new
    used={x for e in edges for x in (e['s'],e['o'])}; N={k:v for k,v in N.items() if k in used}
    removed=[by[i] for i in sorted(rm)]
    return dict(nodes=N,edges=edges),removed
FIXED,REMOVED=build_fixed()
if __name__=='__main__':
    out={m:metrics(M) for m,M in MAPS.items()}; out['llm_fixed']=metrics(FIXED)
    cnt=lambda A:collections.Counter(v[0] for v in A.values())
    out['audit']=dict(llm=dict(n=len(AUD_LLM),by_class=dict(cnt(AUD_LLM)),total=41),peer=dict(n=len(AUD_PEER),by_class=dict(cnt(AUD_PEER)),total=53),expert=dict(n=len(AUD_EXP),by_class=dict(cnt(AUD_EXP)),total=49))
    out['removed']=[(e['id'],e['s'],e['p'],e['o']) for e in REMOVED]
    json.dump(out,open('metrics.json','w'),ensure_ascii=False,indent=1)
    json.dump(dict(nodes=FIXED['nodes'],edges=FIXED['edges']),open('cmap_llm_fixed.json','w'),ensure_ascii=False,indent=1)
    print(json.dumps({k:v for k,v in out.items() if k not in('removed',)},ensure_ascii=False,indent=1)[:4000])
