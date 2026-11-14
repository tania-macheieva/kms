-- BQ1: Яка частка відповідей зі статусом, що збігається з очікуваним, по групах тестів і прогонах?
SELECT r.run_label, t.category_group, COUNT(*) AS n,
       SUM(o.is_match::INT) AS n_match, ROUND(100.0*SUM(o.is_match::INT)/COUNT(*),1) AS status_accuracy_pct
FROM dwh.fact_rag_answer f JOIN dwh.dim_run r USING(run_key) JOIN dwh.dim_outcome o USING(outcome_key)
JOIN dwh.dim_test t USING(test_key)
GROUP BY ALL ORDER BY r.run_label, t.category_group;
-- BQ2: Як вимкнення reranker змінює затримку пошуку й вхідні токени (по ролях)?
SELECT r.run_label, r.reranker_on, ro.role_code, COUNT(*) AS n,
       ROUND(SUM(f.retrieve_ms)/COUNT(*),1) AS avg_retrieve_ms, ROUND(1.0*SUM(f.in_tokens)/COUNT(*)) AS avg_in_tokens
FROM dwh.fact_rag_answer f JOIN dwh.dim_run r USING(run_key) JOIN dwh.dim_role ro USING(role_key)
GROUP BY ALL ORDER BY r.run_label, ro.role_code;
-- BQ3: Яка повнота контексту (context recall = SUM(hit)/SUM(total)) по групах і мові питання?
SELECT r.run_label, t.language_code, t.category_group, COUNT(*) AS n_tests, SUM(f.gold_total) AS gold_total, SUM(f.gold_hit) AS gold_hit,
       ROUND(1.0*SUM(f.gold_hit)/NULLIF(SUM(f.gold_total),0),3) AS context_recall
FROM dwh.fact_rag_answer f JOIN dwh.dim_run r USING(run_key) JOIN dwh.dim_test t USING(test_key)
GROUP BY ALL HAVING SUM(f.gold_total)>0 ORDER BY r.run_label, t.language_code, t.category_group;
-- BQ4: Яка вірність (частка підтриманих тверджень) і скільки невалідних цитат та неціторованих речень по прогонах?
SELECT r.run_label, SUM(f.claims_total) AS claims, SUM(f.claims_supported) AS supported,
       ROUND(1.0*SUM(f.claims_supported)/NULLIF(SUM(f.claims_total),0),3) AS faithfulness,
       SUM(f.n_cited) AS citations, SUM(f.n_invalid) AS invalid_citations, SUM(f.uncited_sent) AS uncited_sentences
FROM dwh.fact_rag_answer f JOIN dwh.dim_run r USING(run_key)
GROUP BY ALL ORDER BY r.run_label;
-- BQ5: Які пари (очікуваний -> фактичний статус) помиляються найчастіше і в якій ролі? (матриця помилок)
SELECT o.expected_status, o.actual_status, ro.role_code, r.run_label, COUNT(*) AS n_errors
FROM dwh.fact_rag_answer f JOIN dwh.dim_outcome o USING(outcome_key) JOIN dwh.dim_role ro USING(role_key) JOIN dwh.dim_run r USING(run_key)
WHERE NOT o.is_match GROUP BY ALL ORDER BY n_errors DESC, r.run_label;
