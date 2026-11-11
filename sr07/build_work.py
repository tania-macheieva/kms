"""Робоча копія OGMS: без зовнішніх імпортів (недоступні офлайн) + мінімальний BFO-каркас (з пам'яті про BFO 2.0, НЕ завантажений)."""
from rdflib import Graph, RDF, RDFS, OWL, URIRef, Literal, BNode
from rdflib.collection import Collection
O='http://purl.obolibrary.org/obo/'
g=Graph(); g.parse('ogms_old.owl',format='xml')
for s,p,o in list(g.triples((None,OWL.imports,None))): g.remove((s,p,o))
B=lambda n:URIRef(O+n)
stub={'BFO_0000001':('entity',None),'BFO_0000002':('continuant','BFO_0000001'),'BFO_0000003':('occurrent','BFO_0000001'),
 'BFO_0000004':('independent continuant','BFO_0000002'),'BFO_0000020':('specifically dependent continuant','BFO_0000002'),
 'BFO_0000031':('generically dependent continuant','BFO_0000002'),'BFO_0000040':('material entity','BFO_0000004'),
 'BFO_0000019':('quality','BFO_0000020'),'BFO_0000017':('realizable entity','BFO_0000020'),'BFO_0000016':('disposition','BFO_0000017'),
 'BFO_0000015':('process','BFO_0000003'),'IAO_0000030':('information content entity','BFO_0000031'),'IAO_0000027':('data item','IAO_0000030')}
for i,(lab,par) in stub.items():
    g.add((B(i),RDF.type,OWL.Class))
    if not g.value(B(i),RDFS.label): g.add((B(i),RDFS.label,Literal(lab+' [BFO stub]')))
    if par and not any(isinstance(x,URIRef) for x in g.objects(B(i),RDFS.subClassOf)): g.add((B(i),RDFS.subClassOf,B(par)))
def disjoint(a,b): g.add((B(a),OWL.disjointWith,B(b)))
for a,b in (('BFO_0000002','BFO_0000003'),('BFO_0000004','BFO_0000020'),('BFO_0000004','BFO_0000031'),('BFO_0000020','BFO_0000031'),('BFO_0000019','BFO_0000017')): disjoint(a,b)
g.add((B('BFO_0000050'),RDF.type,OWL.ObjectProperty)); g.add((B('BFO_0000050'),RDFS.label,Literal('part of [BFO stub]')))
g.serialize('ogms_work.owl',format='xml'); print(len(g))
