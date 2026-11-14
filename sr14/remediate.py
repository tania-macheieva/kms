#!/usr/bin/env python3
"""Усунення дефектів, знайдених метриками S1 -> копія data_s2/ (оригінал data/ не змінюється)."""
import json,shutil,os,re,sys
sys.path.insert(0,'.'); import kms_quality as q
src,dst='data','data_s2'
if os.path.exists(dst): shutil.rmtree(dst)
shutil.copytree(src,dst)
C,M=q.load(src); log=dict(fixed_section=[],fixed_title=[],dropped_duplicates=[])
_,pairs=q.m3_uniqueness(C); drop={b:a for a,b in pairs}   # лишаємо перший у порядку корпусу
for c in C:
    if not c['section'].strip(): c['section']='Preamble'; log['fixed_section'].append(c['chunk_id'])
    if c['title'].startswith('REPLACE VALUE OF GITHUB_TAG'): c['title']=c['doc_id']; log['fixed_title'].append(c['chunk_id'])
for d,m in M.items():
    if m['title'].startswith('REPLACE VALUE OF GITHUB_TAG'): m['title']=d
kept=[c for c in C if c['chunk_id'] not in drop]; log['dropped_duplicates']=[[b,'duplicate_of',a] for b,a in drop.items()]
with open(f'{dst}/corpus.jsonl','w',encoding='utf-8') as f:
    for c in kept: f.write(json.dumps(c,ensure_ascii=False)+'\n')
json.dump(list(M.values()),open(f'{dst}/docs_manifest.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
# вплив на оцінювальні прогони
used=set()
for k in ['results_A.json','results_B.json','sr11_results.json']:
    for r in json.load(open(f'{src}/eval/{k}')): used|=set(r.get('context_ids',[]))|set(r.get('cited',[]))
log['dropped_but_used_in_eval_runs']=sorted(set(drop)&used)
json.dump(log,open('snap/remediation_log.json','w'),ensure_ascii=False,indent=1)
print({k:len(v) for k,v in log.items()}); print(log['dropped_but_used_in_eval_runs'])
