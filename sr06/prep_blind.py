import json, random
from pathlib import Path
B=str(Path(__file__).resolve().parent) + '/'
def load_expert():
    e=json.load(open(B+'models/cmap_expert.json')); return e['concepts'],e['propositions']
def load_peer():
    e=json.load(open(B+'models/cmap_peer.json')); return e['concepts'],e['propositions']
def load_llm():
    tr=[json.loads(l) for l in open(B+'models/triples_llm.jsonl')]
    labs=[]; 
    for t in tr:
        for x in (t['s'],t['o']):
            if x not in labs: labs.append(x)
    ids={l:f"N{i+1:02d}" for i,l in enumerate(labs)}
    inst=lambda l: any(ch in l for ch in '<>')
    concepts=[dict(id=ids[l],label=l,kind='instance' if inst(l) else 'concept') for l in labs]
    props=[dict(id=t['id'],s=ids[t['s']],p=t['p'],o=ids[t['o']],cross=False,explanation='') for t in tr]
    return concepts,props
MAPS={'expert':load_expert(),'llm':load_llm(),'peer':load_peer()}
def render(c,p):
    lab={x['id']:x['label'] for x in c}
    lines=[f"Понять: {sum(1 for x in c if x['kind']=='concept')}; екземплярів (конкретні значення): {sum(1 for x in c if x['kind']!='concept')}; пропозицій: {len(p)}","","Екземпляри: "+"; ".join(x['label'] for x in c if x['kind']!='concept'),"","Пропозиції (суб'єкт —відношення→ об'єкт):"]
    for q in p: lines.append(f"- {lab[q['s']]} —{q['p']}→ {lab[q['o']]}"+(f"   [КРОС-ЗВ'ЯЗОК між кластерами; пояснення: {q['explanation']}]" if q.get('cross') else ""))
    return "\n".join(lines)
rng=random.Random(2026); letters=['A','B','C']; 
out={}
for who,seed in (('R1',11),('R2',22)):
    r=random.Random(seed); keys=['expert','llm','peer']; r.shuffle(keys)
    out[who]=dict(zip(['A','B','C'],keys))
json.dump(out,open('letters.json','w'),indent=1)
rub=open('rubric_text.md').read() if False else None
for who in ('R1','R2'):
    txt=[]
    for L in 'ABC':
        c,p=MAPS[out[who][L]]; txt.append(f"=== КАРТА {L} ===\n"+render(c,p))
    open(f'input_{who}.txt','w').write("\n\n".join(txt))
print(out); print(len(open('input_R1.txt').read()))
