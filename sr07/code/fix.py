"""Застосовує виправлення A–D до ogms_work.owl -> ogms_fixed.owl"""
import rdflib, json
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import RDF, RDFS, OWL
g=rdflib.Graph(); g.parse('../ogms_work.owl')
L={str(o):s for s,o in g.subject_objects(RDFS.label)}
lab=lambda s:L[s]
BFO=lambda n:URIRef('http://purl.obolibrary.org/obo/'+n)
log=[]
# --- Fix A: дизʼюнктність
for a,b in [('normal homeostasis','abnormal homeostasis'),('chronic disease course','transient disease course'),
            ('inpatient encounter','outpatient encounter'),('health care process','ancillary health care process')]:
    g.add((lab(a),OWL.disjointWith,lab(b))); log.append(f'A: disjoint({a}, {b})')
# --- Fix B: disease stage  is-a disease course  ->  is-a process AND part_of some disease course
ds=lab('disease stage'); dc=lab('disease course')
g.remove((ds,RDFS.subClassOf,dc)); g.add((ds,RDFS.subClassOf,BFO('BFO_0000015')))
r=BNode(); g.add((r,RDF.type,OWL.Restriction)); g.add((r,OWL.onProperty,BFO('BFO_0000050'))); g.add((r,OWL.someValuesFrom,dc)); g.add((ds,RDFS.subClassOf,r))
log.append('B: disease stage: -subClassOf disease course; +subClassOf process; +subClassOf part_of some disease course')
# --- Fix C: pain під bodily process, а не під symptom
pain=lab('pain'); g.remove((pain,RDFS.subClassOf,lab('symptom'))); g.add((pain,RDFS.subClassOf,lab('bodily process')))
log.append('C: pain: -subClassOf symptom; +subClassOf bodily process')
# --- Fix D: іменування/метадані
for c,l in list(g.subject_objects(RDFS.label)):
    if str(l)!=str(l).strip():
        g.set((c,RDFS.label,Literal(str(l).strip()))); log.append(f'D: trim label "{l}"')
    if str(l)=='_undefined primitive term':
        g.set((c,RDFS.label,Literal('undefined primitive term'))); log.append('D: rename label _undefined primitive term -> undefined primitive term')
DEF=URIRef('http://purl.obolibrary.org/obo/IAO_0000115')
for c,d in list(g.subject_objects(DEF)):
    s=str(d)
    if 'data itme' in s or 'an spatial' in s:
        g.set((c,DEF,Literal(s.replace('data itme','data item').replace('an spatial','a spatial')))); log.append(f'D: typo fixed in definition of "{g.value(c,RDFS.label)}"')
old=ds; new=URIRef('http://purl.obolibrary.org/obo/OGMS_9000001')  # локальний тимчасовий ID, не офіційний
for s,p,o in list(g):
    if s==old or o==old:
        g.remove((s,p,o)); g.add((new if s==old else s,p,new if o==old else o)) if True else None
log.append('D: IRI ogms.owl#disease_stage -> obo/OGMS_9000001 (тимчасовий локальний ID)')
g.serialize('../ogms_fixed.owl',format='xml')
json.dump(log,open('../fix_log.json','w'),ensure_ascii=False,indent=1); print('\n'.join(log))
