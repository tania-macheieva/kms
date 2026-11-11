"""Мінімальний бенчмарк: Kuzu (Cypher, LPG) vs Oxigraph (SPARQL, RDF) + незалежна перевірка у чистому Python.
Це НЕ Neo4j/Memgraph/GraphDB — лише їх представники за моделлю даних (див. звіт)."""
import csv, json, time, statistics, os, shutil, tempfile, collections
import kuzu, pyoxigraph as ox
DATA='../data/'
def rd(f,h=False):
    r=list(csv.reader(open(DATA+f+'.csv')));
    return r[1:] if h else r
nodes={t:rd(t,True) for t in ['disease','drug','gene','symptom']}
E={k:rd(k) for k in ['subclass','treats','assoc','hassym','interacts']}
# ---------- параметри запитів (обрані за даними, щоб результати були непорожні)
cnt=collections.Counter(d for r,d in E['treats']); P_D=cnt.most_common(1)[0][0]
dr_genes=collections.Counter(r for r,d in E['treats']); P_R=dr_genes.most_common(1)[0][0]
deep=None; par=dict(E['subclass'])
def depth(x):
    n=0
    while x in par: x=par[x]; n+=1
    return n
P_ANC=max((x for x in par),key=depth)
ag=collections.Counter(d for d,g in E['assoc']); P_CO=ag.most_common(1)[0][0]
print('params',dict(disease=P_D,drug=P_R,anc=P_ANC,anc_depth=depth(P_ANC),co=P_CO))
# ---------- ground truth (чистий Python)
T=collections.defaultdict(set)
for r,d in E['treats']: T[d].add(r)
A=collections.defaultdict(set)
for d,g in E['assoc']: A[d].add(g)
gt={}
gt['Q1']=sorted(T[P_D])
gt['Q2']=sorted({g for r,d in E['treats'] if r==P_R for g in A[d]})
gt['Q3']=[(d,n) for d,n in sorted(((d,len(v)) for d,v in T.items()),key=lambda x:(-x[1],x[0]))[:10]]
anc=[];x=P_ANC
while x in par: x=par[x]; anc.append(x)
gt['Q4']=sorted(set(anc))
gt['Q5']=sorted([(o,len(A[P_CO]&A[o])) for o in A if o!=P_CO and len(A[P_CO]&A[o])>=2],key=lambda t:(-t[1],t[0]))
# ---------- Kuzu
tmp=tempfile.mkdtemp(); t0=time.perf_counter()
db=kuzu.Database(os.path.join(tmp,'k')); cn=kuzu.Connection(db)
for t,l in [('Disease','disease'),('Drug','drug'),('Gene','gene'),('Symptom','symptom')]:
    cn.execute(f'CREATE NODE TABLE {t}(id STRING PRIMARY KEY, name STRING)')
for r,(a,b) in [('TREATS',('Drug','Disease')),('ASSOC_GENE',('Disease','Gene')),('HAS_SYMPTOM',('Disease','Symptom')),('SUBCLASS_OF',('Disease','Disease')),('INTERACTS',('Drug','Drug'))]:
    cn.execute(f'CREATE REL TABLE {r}(FROM {a} TO {b})')
ab=os.path.abspath(DATA)
for t,l in [('Disease','disease'),('Drug','drug'),('Gene','gene'),('Symptom','symptom')]: cn.execute(f"COPY {t} FROM '{ab}/{l}.csv' (HEADER=true)")
for r,f in [('TREATS','treats'),('ASSOC_GENE','assoc'),('HAS_SYMPTOM','hassym'),('SUBCLASS_OF','subclass'),('INTERACTS','interacts')]: cn.execute(f"COPY {r} FROM '{ab}/{f}.csv' (HEADER=false)")
load_k=time.perf_counter()-t0
CY={
'Q1':f"MATCH (r:Drug)-[:TREATS]->(d:Disease {{id:'{P_D}'}}) RETURN r.id AS a ORDER BY a",
'Q2':f"MATCH (r:Drug {{id:'{P_R}'}})-[:TREATS]->(d:Disease)-[:ASSOC_GENE]->(g:Gene) RETURN DISTINCT g.id AS a ORDER BY a",
'Q3':"MATCH (r:Drug)-[:TREATS]->(d:Disease) RETURN d.id AS a, count(r) AS n ORDER BY n DESC, a LIMIT 10",
'Q4':f"MATCH (d:Disease {{id:'{P_ANC}'}})-[:SUBCLASS_OF*1..30]->(x:Disease) RETURN DISTINCT x.id AS a ORDER BY a",
'Q5':f"MATCH (d:Disease {{id:'{P_CO}'}})-[:ASSOC_GENE]->(g:Gene)<-[:ASSOC_GENE]-(o:Disease) WHERE o.id <> '{P_CO}' WITH o, count(DISTINCT g) AS s WHERE s >= 2 RETURN o.id AS a, s ORDER BY s DESC, a"}
# ---------- Oxigraph
EX='http://example.org/'; iri=lambda x:ox.NamedNode(EX+x)
t0=time.perf_counter(); st=ox.Store()
for t,rows in nodes.items():
    cls=t.capitalize()
    for i,n in rows: st.add(ox.Quad(iri(i),ox.NamedNode('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),iri(cls),ox.DefaultGraph())); st.add(ox.Quad(iri(i),ox.NamedNode('http://www.w3.org/2000/01/rdf-schema#label'),ox.Literal(n),ox.DefaultGraph()))
for k,p in [('subclass','subclassOf'),('treats','treats'),('assoc','assocGene'),('hassym','hasSymptom'),('interacts','interacts')]:
    for a,b in E[k]: st.add(ox.Quad(iri(a),iri(p),iri(b),ox.DefaultGraph()))
load_o=time.perf_counter()-t0
PRE=f'PREFIX ex: <{EX}>\n'
SP={
'Q1':PRE+f"SELECT ?a WHERE {{ ?r ex:treats ex:{P_D} . BIND(STRAFTER(STR(?r),'{EX}') AS ?a) }} ORDER BY ?a",
'Q2':PRE+f"SELECT DISTINCT ?a WHERE {{ ex:{P_R} ex:treats ?d . ?d ex:assocGene ?g . BIND(STRAFTER(STR(?g),'{EX}') AS ?a) }} ORDER BY ?a",
'Q3':PRE+f"SELECT ?a (COUNT(?r) AS ?n) WHERE {{ ?r ex:treats ?d . BIND(STRAFTER(STR(?d),'{EX}') AS ?a) }} GROUP BY ?a ORDER BY DESC(?n) ?a LIMIT 10",
'Q4':PRE+f"SELECT DISTINCT ?a WHERE {{ ex:{P_ANC} ex:subclassOf+ ?x . BIND(STRAFTER(STR(?x),'{EX}') AS ?a) }} ORDER BY ?a",
'Q5':PRE+f"SELECT ?a (COUNT(DISTINCT ?g) AS ?s) WHERE {{ ex:{P_CO} ex:assocGene ?g . ?o ex:assocGene ?g . FILTER(?o != ex:{P_CO}) BIND(STRAFTER(STR(?o),'{EX}') AS ?a) }} GROUP BY ?a HAVING (COUNT(DISTINCT ?g) >= 2) ORDER BY DESC(?s) ?a"}
def run_k(q): 
    r=cn.execute(q); rows=[]
    while r.has_next(): rows.append(tuple(r.get_next()))
    return rows
def run_o(q):
    rows=[]
    for sol in st.query(q):
        vals=[sol[v] for v in sol.variables] if hasattr(sol,'variables') else list(sol)
        out=[]
        for v in vals: out.append(int(v.value) if getattr(v,'datatype',None) and v.datatype.value.endswith('integer') else v.value)
        rows.append(tuple(out))
    return rows
def norm(rows,q):
    if q in('Q1','Q2','Q4'): return sorted(r[0] for r in rows)
    return [(r[0],int(r[1])) for r in rows]
def timeit(f,n=30):
    ts=[]
    for _ in range(n):
        t=time.perf_counter(); res=f(); ts.append((time.perf_counter()-t)*1000)
    return res,ts
out={'params':dict(disease=P_D,drug=P_R,anc=P_ANC,co=P_CO),'load_s':{'kuzu':round(load_k,3),'oxigraph':round(load_o,3)},'queries':{}}
for q in ['Q1','Q2','Q3','Q4','Q5']:
    rk,tk=timeit(lambda:run_k(CY[q])); ro,to=timeit(lambda:run_o(SP[q]))
    nk,no=norm(rk,q),norm(ro,q); g=gt[q]
    out['queries'][q]=dict(rows=len(g),kuzu_eq_truth=nk==g,oxi_eq_truth=no==g,kuzu_eq_oxi=nk==no,
      kuzu_first_ms=round(tk[0],2),kuzu_med_ms=round(statistics.median(tk[1:]),2),kuzu_p95_ms=round(sorted(tk[1:])[int(.95*len(tk[1:]))-1],2),
      oxi_first_ms=round(to[0],2),oxi_med_ms=round(statistics.median(to[1:]),2),oxi_p95_ms=round(sorted(to[1:])[int(.95*len(to[1:]))-1],2),cypher=CY[q],sparql=SP[q])
    print(q,{k:v for k,v in out['queries'][q].items() if k not in('cypher','sparql')})
b12=run_k(CY['Q4'].replace('*1..30','*1..12')); out['q4_bound12']=dict(rows=len(b12),truth_rows=len(gt['Q4']),depth_of_param=depth(P_ANC))
print('Q4 bound 12 ->',len(b12),'of',len(gt['Q4']))
json.dump(out,open('../bench_results.json','w'),ensure_ascii=False,indent=1); shutil.rmtree(tmp)
print('load',out['load_s'])
