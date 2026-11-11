"""OOPS!-подібні перевірки (НЕ сервіс OOPS!). Використання: python pitfalls.py file.owl"""
import sys, re, json, rdflib
from rdflib.namespace import RDF, RDFS, OWL
DEF=rdflib.URIRef('http://purl.obolibrary.org/obo/IAO_0000115')
LIC=[rdflib.URIRef('http://purl.org/dc/terms/license'),rdflib.URIRef('http://purl.org/dc/elements/1.1/rights')]
def run(path):
    g=rdflib.Graph(); g.parse(path)
    cls=[c for c in g.subjects(RDF.type,OWL.Class) if isinstance(c,rdflib.URIRef)]
    og=[c for c in cls if '/OGMS_' in str(c) or 'ogms.owl#' in str(c)]  # власні класи (без BFO/IAO-заглушок)
    lab=lambda c:str(g.value(c,RDFS.label) or c)
    res={}
    # P04: ізольовані класи (немає ні батька, ні дітей)
    par={c:set(o for o in g.objects(c,RDFS.subClassOf) if isinstance(o,rdflib.URIRef)) for c in cls}
    kids={c:set() for c in cls}
    for c,ps in par.items():
        for p in ps: kids.setdefault(p,set()).add(c)
    res['P04 ізольовані класи']=[lab(c) for c in og if not par[c] and not kids.get(c)]
    # P06 цикли у subClassOf
    def reach(c,seen=()):
        for p in par.get(c,()):
            if p in seen or p==c: return True
            if reach(p,seen+(c,)): return True
        return False
    res['P06 цикли is-a']=[lab(c) for c in og if reach(c)]
    # P08 відсутні/заглушкові визначення
    nodef=[];todo=[]
    for c in og:
        d=g.value(c,DEF)
        if d is None: nodef.append(lab(c))
        elif str(d).strip().upper().startswith('TODO'): todo.append(lab(c))
    res['P08a без визначення']=nodef; res['P08b визначення TODO']=todo
    # P10 відсутня дизʼюнктність: сестринські класи (≥2 дітей) без жодної disjointWith
    dis=set()
    for a,b in g.subject_objects(OWL.disjointWith): dis|={a,b}
    res['P10 група сестер без disjointWith']=sorted({lab(p) for p in kids if len(kids[p])>1 and p in cls and not any(k in dis for k in kids[p]) and p in og+[x for x in cls]} & {lab(p) for p in og})
    # P22 стиль іменування
    bad=[l for l in map(lab,og) if l!=l.strip() or l.startswith('_') or re.search(r'[A-Z]{2,}',l)]
    res['P22 іменування (пробіли/_/абревіатури)']=bad
    # P32 однакові мітки
    from collections import Counter
    cnt=Counter(lab(c) for c in og); res['P32 дублі міток']=[k for k,v in cnt.items() if v>1]
    # P36 розширення файлу в IRI
    res['P36 IRI з .owl#']=[lab(c) for c in og if '.owl#' in str(c)]
    # P41 ліцензія
    onts=list(g.subjects(RDF.type,OWL.Ontology))
    res['P41 немає ліцензії']=[] if any((o,l,None) in g for o in onts for l in LIC) else ['ontology header']
    # друкарські помилки (словник відомих помилок цього знімка — знайдено вручну)
    res['TYPO у визначеннях']=[lab(c) for c in og if re.search(r'\bitme\b|\ban spatial\b',str(g.value(c,DEF) or ''))]
    return len(og),res
if __name__=='__main__':
    n,r=run(sys.argv[1]); print('own classes',n)
    for k,v in r.items(): print(f'{k}: {len(v)}', v[:12])
