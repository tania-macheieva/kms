"""Спрощена перевірка OntoClean. Теги R(ригідність)/U(критерій єдності) призначені АВТОРОМ вручну (судження, не формальна верифікація)."""
import sys, json, rdflib
from rdflib.namespace import RDFS, RDF, OWL
TAGS={ # label: (R, U-criterion or None)
 'disease course':('+R','totality of processes of one disease instance'),
 'disease stage':('+R','temporal part of a course'),
 'relapse':('+R','temporal part of a course'),'remission':('+R','temporal part of a course'),
 'symptom':('-R',None),'sign':('-R',None),'vital sign':('-R',None),
 'pain':('+R','single bodily process'),
 'bodily process':('+R','single bodily process'),
 'homeostasis':('+R',None),'normal homeostasis':('-R',None),'abnormal homeostasis':('-R',None),
 'chronic disease course':('+R','totality of processes of one disease instance'),
 'acute disease course':('+R','totality of processes of one disease instance'),
 'transient disease course':('+R','totality of processes of one disease instance'),
 'progressive disease course':('+R','totality of processes of one disease instance'),
 'process [BFO stub]':('+R','single process'),
}
def check(path):
    g=rdflib.Graph(); g.parse(path)
    lab={str(o):s for s,o in g.subject_objects(RDFS.label)}
    ilab={s:str(o) for s,o in g.subject_objects(RDFS.label)}
    viol=[]; ok=0
    for ch,(rc,uc) in TAGS.items():
        for p in g.objects(lab[ch],RDFS.subClassOf):
            if not isinstance(p,rdflib.URIRef): continue
            pl=ilab.get(p); 
            if pl not in TAGS: continue
            rp,up=TAGS[pl]; bad=[]
            if rp=='-R' and rc=='+R': bad.append('анти-ригідний батько підкласифікує ригідний клас')
            if up and uc!=up and pl not in ('process [BFO stub]',):
                bad.append(f'критерій єдності батька «{up}» не успадковано: «{uc}»')
            if bad: viol.append((ch,pl,'; '.join(bad)))
            else: ok+=1
    return viol,ok
if __name__=='__main__':
    out={}
    for k,p in (('before','../ogms_work.owl'),('after','../ogms_fixed.owl')):
        v,ok=check(p); out[k]={'violations':v,'ok_edges':ok}; print(k,ok,v)
    json.dump({'tags':TAGS,**out},open('../ontoclean_results.json','w'),ensure_ascii=False,indent=1)
