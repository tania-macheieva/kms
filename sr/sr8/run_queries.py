#!/usr/bin/env python3
"""Запуск запитів до WDQS / DBpedia на ВАШОМУ комп'ютері.
python run_queries.py queries results      # мої запити
python run_queries.py llm_queries results_llm   # запити LLM
Ключів API не потрібно. Пауза між запитами — ввічливість до публічного сервісу."""
import sys, os, glob, json, time, urllib.request, urllib.parse
WD='https://query.wikidata.org/sparql'; DB='https://dbpedia.org/sparql'
src,dst=sys.argv[1],sys.argv[2]; os.makedirs(dst,exist_ok=True)
for f in sorted(glob.glob(os.path.join(src,'*.rq'))):
    name=os.path.basename(f)[:-3]; q=open(f,encoding='utf-8').read()
    ep=DB if 'dbpedia.org/ontology' in q else WD
    url=ep+'?'+urllib.parse.urlencode({'query':q,'format':'json'})
    req=urllib.request.Request(url,headers={'Accept':'application/sparql-results+json','User-Agent':'student-sr8/1.0 (educational)'})
    t=time.time()
    try:
        data=json.load(urllib.request.urlopen(req,timeout=70)); status='ok'
    except Exception as e:
        data={'error':str(e)}; status='error'
    dt=round(time.time()-t,1)
    rows=data.get('results',{}).get('bindings',[]) if status=='ok' else []
    out={'name':name,'status':status,'seconds':dt,'boolean':data.get('boolean'),'n_rows':len(rows),'head':rows[:5],'error':data.get('error')}
    json.dump(out,open(os.path.join(dst,name+'.json'),'w'),ensure_ascii=False,indent=1)
    print(name,status,dt,'s rows=',len(rows),'bool=',data.get('boolean'),data.get('error') or '')
    time.sleep(2)
