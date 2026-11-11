import json
from docx import Document
from docx.shared import Pt, Cm
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
B=json.load(open('../bench_results.json')); L=json.load(open('../llm_eval_results.json'))
V='✔ джерело'; M='⚠ зі спогаду'
CR=[('1 Модель даних','LPG (граф властивостей)','LPG','RDF-тріплстор',V+': db-engines'),
('2 Мова запитів','Cypher, Bolt, HTTP, Java API','Cypher (заявлена сумісність із Neo4j), Bolt-драйвери','SPARQL 1.1, GraphQL',V+': db-engines, README'),
('3 ACID','ACID','ACID, snapshot isolation','ACID',V+': db-engines'),
('4 Масштабування','Raft-кластер (лише Enterprise), Fabric','Raft HA; шардинг (db-engines)','Multi-source replication; шардингу немає',V+': db-engines'),
('5 Алгоритми','Бібліотека GDS',' MAGE: 40+ алгоритмів (PageRank, спільноти…)','SPARQL property paths, RDFS/OWL-виведення','Memgraph '+V+'; Neo4j і GraphDB '+M),
('6 Інтеграція з LLM','Векторний індекс, GraphRAG','Векторні індекси, GraphRAG','Конектори для LLM/ретрівалу','Memgraph '+V+'; решта '+M),
('7 Ліцензія','GPLv3 (Community) + комерційна','BSL 1.1 (Community) + enterprise-ліцензія','GraphDB Free (некомерційна) + комерційна',V+': db-engines, README'),
('8 Експлуатація','Java, дисковий, довговічний','C/C++, in-memory + snapshots/WAL; обмежений обсягом RAM','Java, Workbench (GUI), довговічний','Memgraph/ліцензії '+V+'; GUI '+M)]
BN=[]
for q,v in B['queries'].items():
    BN.append((q,v['rows'],'так' if v['kuzu_eq_truth'] else 'ні','так' if v['oxi_eq_truth'] else 'ні','так' if v['kuzu_eq_oxi'] else 'ні',v['kuzu_first_ms'],v['kuzu_med_ms'],v['oxi_first_ms'],v['oxi_med_ms'],'так' if L[q]['equal'] else 'ні'))
LIM=['Neo4j, Memgraph і GraphDB НЕ запускалися (дистрибутиви недоступні; Docker-демон не працює). Замість них — Kuzu (LPG+Cypher) і Oxigraph (RDF+SPARQL) як представники моделей. Їхній час НЕ переноситься на три цільові сховища.',
'Дані синтетичні (600 вузлів, 2915 ребер), не реальна медицина; навантаження крихітне — різниця архітектур майже непомітна.',
'Обидва рушії вбудовані (в одному процесі), без мережі й без паралельних клієнтів; 2 vCPU; 30 повторів, перший (холодний) запуск окремо; записи й транзакції не вимірювались.',
'Критерії 5–8 частково зі спогаду (позначено ⚠); перевірте за документацією сховищ.',
'Зручність (C3) оцінено лише для Kuzu/Oxigraph; для трьох цільових заповнюйте після запуску bench_external.py (він не тестувався).']
wb=Workbook(); wb.remove(wb.active); HF=Font(bold=True,color='FFFFFF'); FL=PatternFill('solid',fgColor='305496'); W=Alignment(wrap_text=True,vertical='top')
def sh(n,h,r,w):
    ws=wb.create_sheet(n); ws.append(h)
    for c in ws[1]: c.font=HF; c.fill=FL; c.alignment=W
    for x in r: ws.append(list(x))
    for i,v in enumerate(w): ws.column_dimensions[chr(65+i)].width=v
    for row in ws.iter_rows(min_row=2):
        for c in row: c.alignment=W
sh('Критерії',['Критерій','Neo4j','Memgraph','GraphDB','Статус джерела'],CR,[20,34,40,36,34])
sh('Бенчмарк',['Запит','Рядків','Kuzu = еталон','Oxigraph = еталон','Kuzu = Oxigraph','Kuzu 1-й, мс','Kuzu медіана, мс','Oxi 1-й, мс','Oxi медіана, мс','SPARQL від LLM = мій'],BN,[8,8,14,16,16,12,14,12,14,18])
sh('Запити',['Запит','Cypher','SPARQL'],[(q,v['cypher'],v['sparql']) for q,v in B['queries'].items()],[8,90,110])
sh('Обмеження',['Обмеження'],[(x,) for x in LIM],[140])
wb.save('../SR9_graph_db_comparison.xlsx')
d=Document(); s=d.sections[0]; s.page_width=Cm(21); s.page_height=Cm(29.7)
for a in ('left_margin','right_margin'): setattr(s,a,Cm(1.6))
s.top_margin=Cm(1.4); s.bottom_margin=Cm(1.3)
st=d.styles['Normal']; st.font.name='Calibri'; st.font.size=Pt(9); st.element.rPr.rFonts.set(qn('w:eastAsia'),'Calibri'); st.paragraph_format.space_after=Pt(2)
def P(t,b=False,sz=None):
    p=d.add_paragraph(); r=p.add_run(t); r.bold=b
    if sz: r.font.size=Pt(sz)
def shade(c):
    t=c._tc.get_or_add_tcPr(); e=OxmlElement('w:shd'); e.set(qn('w:val'),'clear'); e.set(qn('w:fill'),'D9E2F3'); t.append(e)
def tab(h,r,w):
    t=d.add_table(rows=1,cols=len(h)); t.style='Table Grid'; t.autofit=False
    for i,x in enumerate(h):
        c=t.rows[0].cells[i]; c.text=''; rr=c.paragraphs[0].add_run(x); rr.bold=True; rr.font.size=Pt(8); shade(c)
    for row in r:
        cs=t.add_row().cells
        for i,v in enumerate(row): cs[i].text=''; cs[i].paragraphs[0].add_run(str(v)).font.size=Pt(8)
    for i,x in enumerate(w): t.columns[i].width=Cm(x)
    for row in t.rows:
        for i,x in enumerate(w): row.cells[i].width=Cm(x)
        for c in row.cells:
            for p in c.paragraphs: p.paragraph_format.space_after=Pt(0)
P('Самостійна робота 9. Критерії порівняння графових баз',True,13)
P('Курс «Сховища знань та управління знаннями» · Сценарій: біомедичний граф знань (хвороби — ліки — гени — симптоми)')
P('Статус виконання (важливо)',True,10)
P('Neo4j, Memgraph і GraphDB у середовищі підготовки розгорнути не вдалося (немає доступу до їхніх дистрибутивів, Docker не працює). Тому критерії порівняно за документацією для всіх трьох, а тестовий набір запитів виконано на двох доступних представниках: Kuzu (граф властивостей, Cypher) і Oxigraph (RDF, SPARQL). Скрипт bench_external.py для запуску тих самих запитів на Neo4j, Memgraph і GraphDB додано, але автор його не тестував — його запустіть самі (інструкція в docstring), щоб закрити C1/C2 для цільових сховищ.')
P('1. Критерії (8) — за документацією',True,10)
tab(['Критерій','Neo4j','Memgraph','GraphDB','Джерело'],CR,[2.4,3.7,4.2,3.7,3.7])
P('Джерела: db-engines.com (порівняння GraphDB/Memgraph/Neo4j) і README Memgraph; позначка «зі спогаду» — не перевірено.')
P('2. Датасет і запити',True,10)
P('Синтетичний граф: 200 хвороб, 150 ліків, 150 генів, 100 симптомів = 600 вузлів; 2915 ребер (TREATS, ASSOC_GENE, HAS_SYMPTOM, SUBCLASS_OF, INTERACTS), seed=42. Запити: Q1 точковий пошук, Q2 двокрокове обходження, Q3 агрегація top-10, Q4 транзитивні предки (шлях змінної довжини / property path), Q5 спільні гени (self-join + HAVING). Ті самі запити — Cypher і SPARQL.')
P('3. Результати (мс; медіана з 29 повторів, холодний перший запуск окремо)',True,10)
tab(['Q','Рядків','Kuzu=еталон','Oxi=еталон','Kuzu=Oxi','Kuzu 1-й','Kuzu мед.','Oxi 1-й','Oxi мед.','SPARQL LLM=мій'],BN,[0.9,1.2,1.7,1.7,1.5,1.5,1.6,1.5,1.5,2.3])
P(f"Час завантаження: Kuzu {B['load_s']['kuzu']} с, Oxigraph {B['load_s']['oxigraph']} с. Усі 5 запитів дали однакові результати в обох рушіях і збіглися з незалежним еталоном (чистий Python). Розбіжність знайдено лише в першому варіанті Q4: Cypher зі шляхом *1..12 повернув {B['q4_bound12']['rows']} предків із {B['q4_bound12']['truth_rows']}, бо глибина ієрархії 19, а SPARQL-шлях + необмежений; після *1..30 результати збіглися. Висновок: у Cypher межу глибини треба обирати свідомо.")
P('Зручність: Cypher дав компактніші запити для обходів; SPARQL — стандартний і не потребує схеми, але Q4/Q5 вимагають BIND/STRAFTER для порівняння з ID. Kuzu потребує попередньої схеми (CREATE NODE/REL TABLE), Oxigraph — ні. Oxigraph був у 2–20 разів швидший за медіаною на цих мікрозапитах, але це вбудований рушій без мережі й на мініатюрних даних — вирішальним критерієм це бути не може.')
P('Cypher↔SPARQL за допомогою LLM: слабка LLM (без інструментів) перекладала мої Cypher-запити у SPARQL; всі 5 перекладів виконано, результати ідентичні моїм (5 з 5). Недолік: додано зайві rdf:type-шаблони (безкорисні на цих даних, але витрачають час), а коментар до Q4 хибно прирівнює + до *1..30.')
P('4. Рекомендація для сценарію',True,10)
P('Сценарій: граф знань, що інтегрується з відкритими онтологіями й Wikidata (RDF/OWL, SPARQL, SHACL-валідація, виведення). Рекомендація — GraphDB: RDF-модель і SPARQL — спільний стандарт із цими джерелами, є виведення, ліцензія Free достатня для навчального проєкту. Якщо головне — аналітика шляхів і GraphRAG на властивостях вузлів, краще Neo4j (зрілість, екосистема) або Memgraph (in-memory, MAGE, векторні індекси; обмежений обсягом RAM). Це рекомендація за критеріями та сценарієм, а не за виміряною швидкістю цих трьох сховищ.')
P('5. Самоперевірка',True,10)
P('1) RDF кращий, коли потрібні інтеграція з багатьох джерел (глобальні IRI), відкриті стандарти, виведення за онтологією, SHACL і федеративні запити. 2) Index-free adjacency: вузол зберігає прямі вказівники на сусідні ребра, тож вартість обходу залежить від локальної структури, а не від розміру всього графа; Kuzu реалізує це інакше (колонкове сховище з індексами суміжності), тому поняття не слід ототожнювати з будь-яким графовим рушієм. 3) Обмеження — див. нижче. 4) Для 100× більших даних (60 тис. вузлів, ≈290 тис. ребер — усе ще мало) швидкість треба вимірювати заново; для Memgraph — рахувати RAM, для GraphDB — вартість матеріалізації виведення, для всіх — індекси та межі глибини шляхів; різниця між сховищами проявиться на мільйонах ребер, і цей бенчмарк її не передбачає.')
P('6. Обмеження та декларація використання ШІ',True,10)
P(' '.join(LIM))
P('Модель: Claude (Anthropic). Призначення: розробка скриптів і звіту; «сліпий» LLM — переклад Cypher→SPARQL. Приклад запиту: «Переклади 5 запитів Cypher у SPARQL 1.1 за наведеною схемою RDF». Перевірка: виконання перекладів і порівняння з еталоном у Python; факти про сховища — з db-engines і README Memgraph. Студент має сам запустити тест на Neo4j/Memgraph/GraphDB і перевірити позначені «зі спогаду» критерії.')
d.save('../SR9_report.docx')
