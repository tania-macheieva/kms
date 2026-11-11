"""HermiT до/після виправлень. Проби = додаткові тестові класи/індивід, додані в памʼять (не в файли)."""
import json, time, types
from pathlib import Path
from owlready2 import *
OBO='http://purl.obolibrary.org/obo/'
ROOT=Path(__file__).resolve().parents[1]
def world(path):
    w=World(); o=w.get_ontology(str(Path(path).resolve())).load(); return w,o
def byl(w,label):
    r=[c for c in w.classes() if any(str(l)==label for l in c.label)]; assert len(r)==1,(label,r); return r[0]
def run(path, tag):
    out={}
    w,o=world(path)
    with o:
        probes={
         'P1 normal ⊓ abnormal homeostasis':[byl(w,'normal homeostasis'),byl(w,'abnormal homeostasis')],
         'P2 chronic ⊓ transient disease course':[byl(w,'chronic disease course'),byl(w,'transient disease course')],
         'P3 inpatient ⊓ outpatient encounter':[byl(w,'inpatient encounter'),byl(w,'outpatient encounter')],
         'P4 health care process ⊓ ancillary':[byl(w,'health care process'),byl(w,'ancillary health care process')],
         'P5 disease ⊓ disorder':[byl(w,'disease'),byl(w,'disorder')],
         'P6 pain ⊓ quality(BFO)':[byl(w,'pain'),w['%sBFO_0000019'%OBO]],
        }
        pc={}
        for k,(a,b) in probes.items():
            pc[k]=types.new_class('Probe_'+k[:2],(a,b)); 
    rel=byl(w,'relapse'); dc=byl(w,'disease course'); pain=byl(w,'pain'); occ=w['%sBFO_0000003'%OBO]; sym=byl(w,'symptom'); rem=byl(w,'remission')
    t=time.time(); sync_reasoner_hermit(w,infer_property_values=False); dt=time.time()-t
    inc={c.name for c in w.inconsistent_classes()}; out['unsat_names']=sorted(inc); inc.discard('Nothing')
    out['unsat_probes']={k:(pc[k].name in inc) for k in probes}
    out['n_unsat_total']=len(inc); out['time_s']=round(dt,2)
    out['relapse ⊑ disease course']=dc in rel.ancestors()
    out['remission ⊑ disease course']=dc in rem.ancestors()
    out['pain ⊑ occurrent']=occ in pain.ancestors()
    out['pain ⊑ symptom']=sym in pain.ancestors()
    out['ancestors(pain)']=sorted(a.label[0] if a.label else a.name for a in pain.ancestors() if a is not pain and a is not Thing)
    out['ancestors(relapse)']=sorted(a.label[0] if a.label else a.name for a in rel.ancestors() if a is not rel and a is not Thing)
    # індивід-проба у окремому світі
    w2,o2=world(path)
    with o2:
        ch=byl(w2,'chronic disease course'); tr=byl(w2,'transient disease course')
        x=ch(); x.is_a.append(tr)  # один індивід обох класів
    try:
        sync_reasoner_hermit(w2,infer_property_values=False); out['individual chronic+transient']='consistent'
    except OwlReadyInconsistentOntologyError: out['individual chronic+transient']='INCONSISTENT'
    return out
res={'before':run(ROOT/'ogms_work.owl','before'),'after':run(ROOT/'ogms_fixed.owl','after')}
with (ROOT/'reasoner_results.json').open('w',encoding='utf-8') as f:
    json.dump(res,f,ensure_ascii=False,indent=1)
print(json.dumps(res,ensure_ascii=False,indent=1))
