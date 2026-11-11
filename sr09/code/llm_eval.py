"""Виконує SPARQL, перекладений LLM з Cypher, на тому ж Oxigraph-сховищі; порівнює з еталоном (чистий Python)."""
import csv, json, collections, pyoxigraph as ox
D='../data/'; rd=lambda f,h=False:(lambda r:r[1:] if h else r)(list(csv.reader(open(D+f+'.csv'))))
EX='http://example.org/'; I=lambda x:ox.NamedNode(EX+x); T=ox.NamedNode('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
st=ox.Store()
for t in ['disease','drug','gene','symptom']:
    for i,n in rd(t,True): st.add(ox.Quad(I(i),T,I(t.capitalize()),ox.DefaultGraph()))
for k,p in [('subclass','subclassOf'),('treats','treats'),('assoc','assocGene'),('hassym','hasSymptom'),('interacts','interacts')]:
    for a,b in rd(k): st.add(ox.Quad(I(a),I(p),I(b),ox.DefaultGraph()))
res=json.load(open('../bench_results.json'))
def val(v): return int(v.value) if v.datatype and v.datatype.value.endswith('integer') else v.value
out={}
for q in ['Q1','Q2','Q3','Q4','Q5']:
    rows=[tuple(val(v) for v in list(s)) for s in st.query(open(f'../llm_sparql/{q}.rq').read())]
    mine=[tuple(val(v) for v in list(s)) for s in st.query(res['queries'][q]['sparql'])]
    out[q]={'rows_llm':len(rows),'rows_mine':len(mine),'equal':rows==mine}
    print(q,out[q])
json.dump(out,open('../llm_eval_results.json','w'),indent=1)
