#!/usr/bin/env python3
"""НЕТЕСТОВАНО автором звіту (немає доступу до Neo4j/Memgraph/GraphDB). Запустіть у себе.
  pip install neo4j requests
  docker run -d --name neo4j -p 7687:7687 -e NEO4J_AUTH=neo4j/<ВАШ_ПАРОЛЬ> neo4j:5-community
  docker run -d --name memgraph -p 7688:7687 memgraph/memgraph
  GraphDB Free: запустіть, створіть репозиторій 'sr9' (Workbench), порт 7200
  python bench_external.py neo4j  bolt://localhost:7687 neo4j <ПАРОЛЬ>
  python bench_external.py memgraph bolt://localhost:7688 "" ""
  python bench_external.py graphdb http://localhost:7200/repositories/sr9
Паролі не зберігайте в коді/звіті."""
import sys, csv, json, time, statistics
D='../data/'; rd=lambda f,h=False:(lambda r:r[1:] if h else r)(list(csv.reader(open(D+f+'.csv'))))
R=json.load(open('../bench_results.json'))['queries']; N=30
def timeit(f):
    ts=[];
    for _ in range(N):
        t=time.perf_counter(); res=f(); ts.append((time.perf_counter()-t)*1000)
    return res,round(ts[0],2),round(statistics.median(ts[1:]),2)
kind=sys.argv[1]; out={}
if kind in('neo4j','memgraph'):
    from neo4j import GraphDatabase
    drv=GraphDatabase.driver(sys.argv[2],auth=(sys.argv[3],sys.argv[4]) if sys.argv[3] else None)
    with drv.session() as s:
        s.run('MATCH (n) DETACH DELETE n').consume()
        for L in ['Disease','Drug','Gene','Symptom']:
            if kind=='neo4j': s.run(f'CREATE CONSTRAINT IF NOT EXISTS FOR (n:{L}) REQUIRE n.id IS UNIQUE').consume()
            else: s.run(f'CREATE INDEX ON :{L}(id)').consume()   # різний DDL — фіксуйте як «зручність»
        t=time.perf_counter()
        for L,f in [('Disease','disease'),('Drug','drug'),('Gene','gene'),('Symptom','symptom')]:
            s.run(f'UNWIND $r AS x CREATE (:{L} {{id:x[0],name:x[1]}})',r=rd(f,True)).consume()
        for rel,f,a,b in [('TREATS','treats','Drug','Disease'),('ASSOC_GENE','assoc','Disease','Gene'),('HAS_SYMPTOM','hassym','Disease','Symptom'),('SUBCLASS_OF','subclass','Disease','Disease'),('INTERACTS','interacts','Drug','Drug')]:
            s.run(f'UNWIND $r AS x MATCH (p:{a} {{id:x[0]}}),(q:{b} {{id:x[1]}}) CREATE (p)-[:{rel}]->(q)',r=rd(f)).consume()
        out['load_s']=round(time.perf_counter()-t,3)
        for q,v in R.items():
            f=lambda: [tuple(r.values()) for r in s.run(v['cypher'])]
            res,first,med=timeit(f); out[q]=dict(rows=len(res),first_ms=first,med_ms=med,result=res)
elif kind=='graphdb':
    import requests; ep=sys.argv[2]
    nt=[]
    E='http://example.org/'
    for t in ['disease','drug','gene','symptom']:
        for i,n in rd(t,True): nt.append(f'<{E}{i}> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <{E}{t.capitalize()}> .')
    for k,p in [('subclass','subclassOf'),('treats','treats'),('assoc','assocGene'),('hassym','hasSymptom'),('interacts','interacts')]:
        for a,b in rd(k): nt.append(f'<{E}{a}> <{E}{p}> <{E}{b}> .')
    t=time.perf_counter(); requests.post(ep+'/statements',data='\n'.join(nt).encode(),headers={'Content-Type':'application/n-triples'}).raise_for_status()
    out['load_s']=round(time.perf_counter()-t,3)
    for q,v in R.items():
        def f():
            r=requests.post(ep,data={'query':v['sparql']},headers={'Accept':'application/sparql-results+json'}); r.raise_for_status()
            return [tuple(x['value'] for x in b.values()) for b in r.json()['results']['bindings']]
        res,first,med=timeit(f); out[q]=dict(rows=len(res),first_ms=first,med_ms=med,result=res)
json.dump(out,open(f'../external_{kind}.json','w'),ensure_ascii=False,indent=1); print({k:(v if k=='load_s' else (v['rows'],v['first_ms'],v['med_ms'])) for k,v in out.items()})
