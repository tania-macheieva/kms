import json,re,csv,duckdb,datetime as dt,os
D='src_data/'; os.makedirs('out',exist_ok=True)
if os.path.exists('out/sr12.duckdb'): os.remove('out/sr12.duckdb')
con=duckdb.connect('out/sr12.duckdb'); con.execute(open('sql/ddl.sql').read())
jl=lambda f:{json.loads(l)['id']:json.loads(l) for l in open(D+f)}
T=jl('rag_eval.jsonl'); ST=jl('sr11_tests.jsonl')
R={'A':json.load(open(D+'results_A.json')),'B':json.load(open(D+'results_B.json')),'SR11':json.load(open(D+'sr11_results.json'))}
J={k:{j['id'].split(':',1)[1]:j for j in json.load(open(D+f'judge_{k}_out.json'))} for k in R}
dates={r['id']:r['date'] for r in csv.DictReader(open(D+'log.csv'))}
RUN={'A':('A','lab11',True,dt.date(2026,10,31)),'B':('B','lab11',False,dt.date(2026,11,1)),'SR11':('SR11','sr11',True,dt.date(2026,11,11))}
d=dt.date(2026,10,1)
while d<=dt.date(2026,12,31):
    con.execute("insert into dwh.dim_date values (?,?,?,?,?,?,?,?,?)",[int(d.strftime('%Y%m%d')),d,d.year,(d.month-1)//3+1,d.month,d.strftime('%B'),d.isocalendar()[1],d.day,d.weekday()>=5]); d+=dt.timedelta(1)
for i,(k,(lab,suite,rr,_)) in enumerate(RUN.items(),1):
    con.execute("insert into dwh.dim_run values (?,?,?,?,5,'claude-haiku-4-5 (субагент; фактична модель могла відрізнятися)')",[i,lab,suite,rr])
roles=sorted({r['role'] for v in R.values() for r in v}); 
for i,x in enumerate(roles,1): con.execute("insert into dwh.dim_role values (?,?)",[i,x])
sts=['ANSWER','NO_ANSWER','CONFLICT']; oc={}
for e in sts:
    for a in sts: oc[(e,a)]=len(oc)+1; con.execute("insert into dwh.dim_outcome (outcome_key,expected_status,actual_status) values (?,?,?)",[oc[(e,a)],e,a])
GRP={'answerable':'answerable','simple':'answerable','multi_step':'answerable','cross_lingual':'answerable','no_answer':'no_answer','conflict':'conflict','injection':'unsafe','harmful':'unsafe'}
cyr=re.compile('[А-Яа-яІіЇїЄєҐґ]')
tk={};
def test_key(suite,r,q):
    k=(suite,r['id'])
    if k not in tk:
        tk[k]=len(tk)+1; lang='uk' if cyr.search(q) else 'en'
        con.execute("insert into dwh.dim_test values (?,?,?,?,?,?,?,?)",[tk[k],suite,r['id'],GRP[r['category']],r['category'],r['subtype'],lang,dt.date(2026,10,31) if suite=='lab11' else dt.date(2026,11,11)])
    return tk[k]
n=0
for i,(k,rows) in enumerate(R.items(),1):
    suite=RUN[k][1]; day=RUN[k][3]
    for r in rows:
        t=(T if suite=='lab11' else ST)[r['id']]
        key=test_key(suite,r,t['question'])
        tot=len(t.get('gold_evidence',[]))+len(t.get('gold_ids',[]))
        hit=round(r['context_recall']*tot) if r['context_recall'] is not None else 0
        if r['context_recall'] is None: assert tot==0,(k,r['id'])
        cl=J[k][r['id']]['claims']; sup=sum(c['verdict']=='supported' for c in cl)
        con.execute("insert into dwh.fact_rag_answer values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
          [i,key,int(day.strftime('%Y%m%d')),roles.index(r['role'])+1,oc[(r['expected'],r['status'])],r['in_tokens'],r['out_tokens'],r['retrieve_ms'],r['graph_ms'],r['n_cited'],r['n_invalid'],r['uncited'],len(cl),sup,tot,hit]); n+=1
print('facts',n,'tests',len(tk))
for t in ['dim_date','dim_run','dim_role','dim_outcome','dim_test','fact_rag_answer']: print(t,con.execute(f'select count(*) from dwh.{t}').fetchone()[0])
