import re,duckdb,shutil,tempfile
from pathlib import Path
md=open('llm_proposal.md').read(); ddl=re.search(r"```sql\n(.*?)```",md,re.S).group(1)
def attempt(c,sql,label):
    try: c.execute(sql); print(f'  [OK, прийнято] {label}')
    except Exception as e: print(f'  [ПОМИЛКА] {label}: {type(e).__name__}: {str(e).splitlines()[0][:150]}')
c=duckdb.connect(':memory:'); c.execute(ddl); print('LLM DDL виконано без помилок')
c.execute("insert into dwh.dim_date values (20261031,'2026-10-31',2026,4,10,'October',44,31,true)")
c.execute("insert into dwh.dim_run values (1,'A')")
c.execute("insert into dwh.dim_config values (1,true,5,true,'rag_v1','haiku')")
c.execute("insert into dwh.dim_test_case values (1,'T01','answerable','text','en','2026-10-31','9999-12-31',true)")
for i,r in enumerate(['reader','analyst'],1): c.execute("insert into dwh.dim_role values (?,?)",[i,r])
for i,s in enumerate(['ANSWER','NO_ANSWER'],1): c.execute("insert into dwh.dim_status values (?,?,?)",[i,s,'PROCESSED'])
ins="insert into dwh.fact_evaluation_result (run_key,run_date_key,config_key,test_case_key,role_key,expected_status_key,actual_status_key,is_status_match,input_tokens,output_tokens,retrieval_time_ms,gold_evidence_total,gold_evidence_in_context,context_recall,citation_count,invalid_citation_count,uncited_sentence_count,claim_count,supported_claim_count) values (1,20261031,1,1,{role},1,{act},{m},100,10,5.0,2,1,0.5,1,0,0,1,1)"
print('\nВАДА 1 (зерно): унікальність (run,test,role) дозволяє два рядки для того самого питання в одному прогоні')
attempt(c,ins.format(role=1,act=1,m=1),'рядок 1: T01, прогін A, роль reader')
attempt(c,ins.format(role=2,act=1,m=1),'рядок 2: T01, прогін A, роль analyst (те саме питання!)')
print('  count(*) для одного питання в одному прогоні =',c.execute("select count(*) from dwh.fact_evaluation_result").fetchone()[0],'(має бути 1; accuracy/кількість тестів завищено)')
print('\nВАДА 2 (ключі): SCD2')
attempt(c,"insert into dwh.dim_test_case values (2,'T01','answerable','text','uk','2026-11-12','9999-12-31',true)",'нова версія T01 вставлена, стару забули закрити (is_current/valid_to — збережені прапорці)')
print('  кількість «поточних» версій T01 =',c.execute("select count(*) from dwh.dim_test_case where test_case_id='T01' and is_current").fetchone()[0],'(має бути 1; схема це не забороняє)')
attempt(c,"insert into dwh.dim_test_case values (3,'T01','answerable','text','en','2026-11-05','2026-11-20',false)",'версія з перекриттям періодів (2026-11-05..11-20 перекриває 11-12..9999)')
attempt(c,"update dwh.dim_test_case set is_current=false, valid_to='2026-11-11' where test_case_key=1",'закриття старої версії UPDATE-ом: у DuckDB 2.0.0 для неключових стовпців проходить (застереження LLM виявилось надмірним)')
print('\nВАДА 3 (адитивність/узгодженість): збережені похідні міри')
attempt(c,ins.format(role=2,act=2,m=1).replace('1,20261031,1,1,2','1,20261031,1,2,2'),'is_status_match=1, хоча expected=ANSWER, actual=NO_ANSWER (суперечність)')
d=duckdb.connect('out/sr12.duckdb',read_only=True)
q="""with x as (select r.run_label l, f.gold_hit h, f.gold_total t from dwh.fact_rag_answer f join dwh.dim_run r using(run_key) where f.gold_total>0)
select l, count(*) n, round(avg(1.0*h/t),3) avg_of_row_ratios, round(1.0*sum(h)/sum(t),3) pooled_sum_over_sum from x group by l order by l"""
print('  AVG(context_recall) проти SUM(hit)/SUM(total) на реальних даних:'); print(d.execute(q).df().to_string(index=False))
d.close()
# SCD2 у моїй схемі
with tempfile.TemporaryDirectory(prefix='sr12_') as temp_dir:
    copy_path=Path(temp_dir)/'sr12_copy.duckdb'
    shutil.copyfile('out/sr12.duckdb',copy_path)
    m=duckdb.connect(str(copy_path))
    print('\nМОЯ СХЕМА, SCD2 (демо: тест T24 перекласифіковано 2026-11-12):')
    k=m.execute("select max(test_key)+1 from dwh.dim_test").fetchone()[0]
    attempt(m,f"insert into dwh.dim_test select {k},suite,test_id,category_group,'answerable','paraphrase',language_code,DATE '2026-11-12' from dwh.dim_test where suite='lab11' and test_id='T24' and valid_from=DATE '2026-10-31'",'append-only: нова версія T24')
    print(m.execute("select test_key,test_id,subtype,valid_from,valid_to,is_current from dwh.v_dim_test where test_id='T24'").df().to_string(index=False))
    print(m.execute("select r.run_label,t.test_key,t.subtype from dwh.fact_rag_answer f join dwh.dim_test t using(test_key) join dwh.dim_run r using(run_key) where t.test_id='T24' and t.suite='lab11' order by 1").df().to_string(index=False),'<- старі факти лишилися на версії 1')
    m.close()
