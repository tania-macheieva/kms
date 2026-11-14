from docx import Document
from docx.shared import Pt,Cm,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
d=Document(); s=d.sections[0]; s.page_width=Cm(21); s.page_height=Cm(29.7)
for a in ('left_margin','right_margin'): setattr(s,a,Cm(1.5))
s.top_margin=Cm(1.2); s.bottom_margin=Cm(1.1)
st=d.styles['Normal']; st.font.name='Calibri'; st.font.size=Pt(8.5); st.element.rPr.rFonts.set(qn('w:eastAsia'),'Calibri')
st.paragraph_format.space_after=Pt(1.5); st.paragraph_format.space_before=Pt(0); st.paragraph_format.line_spacing=1.0
def P(t='',b=False,size=None,al=None):
    p=d.add_paragraph(); 
    parts=t.split('**')
    for i,x in enumerate(parts):
        r=p.add_run(x); r.bold=b or i%2==1
        if size: r.font.size=Pt(size)
    if al: p.alignment=al
    return p
def H(t):
    p=P(t,True,9.5); p.paragraph_format.space_before=Pt(3); p.runs[0].font.color.rgb=RGBColor(0x1F,0x3A,0x6E)
def shade(c,col):
    tcPr=c._tc.get_or_add_tcPr(); sh=OxmlElement('w:shd'); sh.set(qn('w:val'),'clear'); sh.set(qn('w:fill'),col); tcPr.append(sh)
def T(rows,w,hdr=True,fs=7.5):
    t=d.add_table(rows=len(rows),cols=len(w)); t.style='Table Grid'; t.autofit=False
    for i,r in enumerate(rows):
        for j,x in enumerate(r):
            c=t.cell(i,j); c.width=Cm(w[j]); c.text=''
            p=c.paragraphs[0]; p.paragraph_format.space_after=Pt(0)
            for k,y in enumerate(x.split('**')):
                rr=p.add_run(y); rr.font.size=Pt(fs); rr.bold=(hdr and i==0) or k%2==1
            if hdr and i==0: shade(c,'DCE6F5')
    for j,x in enumerate(w): t.columns[j].width=Cm(x)
    return t
P('Самостійна робота 12 — Проєктування зіркової схеми',True,13)
P('Курс «Сховища знань та управління знаннями» · домен: медицина / біомедичні дані (біоінформатичні інструкції) · студент: ________ · 12.11.2026',size=8)
H('1. Процес і 5 бізнес-питань')
P('**Процес:** автоматичне оцінювання відповідей RAG-асистента (ЛР11 і СР11) на тестових питаннях по документації bcftools / nf-core Sarek. Дані — реальні результати 3 прогонів (A: reranker увімкнено, 34 питання, 31.10; B: reranker вимкнено, 34, 01.11; SR11: 20 питань, 11.11) = **88 рядків факту**, не синтетика. Процес навмисно відмінний від «variant calling» з ЛР12.')
P('**BQ1** Яка частка відповідей зі статусом, що збігається з очікуваним, по групах тестів і прогонах? **BQ2** Як вимкнення reranker змінює затримку пошуку та вхідні токени по ролях? **BQ3** Яка повнота контексту (context recall) по групах і мові питання? **BQ4** Яка вірність (частка підтриманих тверджень), скільки невалідних цитат і речень без цитат по прогонах? **BQ5** Які пари «очікуваний → фактичний статус» помиляються частіше і в якій ролі?')
H('2. Зерно та обґрунтування')
P('**Зерно: один рядок факту = одне тестове питання, виконане в одному прогоні** (PK = run_key + test_key). Зерно визначено першим, бо від нього залежить, що означає кожна міра і який вимір можна приєднати без дублювання: усі 5 питань рахуються «на відповідь», тож дрібніше (на твердження) пропало б для BQ1/BQ2, а грубіше (на прогін) — для BQ5. Роль користувача — атрибут запуску (FK), а не частина зерна: у кожному прогоні питання виконується однією роллю.')
H('3. Виміри, ієрархії, SCD')
T([['Вимір','Ключові атрибути','Ієрархія / роль','SCD'],
['dim_run','run_label, suite, reranker_on, top_k, generator_model','плоский; несе конфігурацію','0'],
['dim_test','suite, test_id, category_group, category, subtype, language_code, valid_from','category_group → category → subtype → test_id; мова — окремий атрибут','**2** (append-only + view v_dim_test)'],
['dim_date','full_date, рік, квартал, місяць, iso_week','дата → місяць → квартал → рік; iso_week — окрема гілка; роль «дата прогону»','0'],
['dim_role','role_code (reader, analyst, clinician)','плоский','1'],
['dim_outcome (junk)','expected_status, actual_status, is_match (generated)','status → is_match; 9 комбінацій 3×3','0']],[2.6,6.3,6.9,2.2])
P('Схема **зіркова** (виміри не нормалізовано): JOIN короткі, а «сніжинка» (окремі таблиці category/subtype) дала б зайві JOIN при ~54 тестах без виграшу в просторі. **SCD2:** якщо тест перекласифікують, додається нова версія з новим test_key і valid_from; старі факти залишаються на старій версії (перевірено, flaws_demo_output.txt). valid_to та is_current обчислює view, а не зберігаються.')
H('4. Міри та адитивність')
T([['Міра','Тип','Міра','Тип'],
['in_tokens, out_tokens, retrieve_ms, graph_ms','адитивні (SUM; середнє = SUM/COUNT)','claims_total, claims_supported','адитивні'],
['n_cited, n_invalid, uncited_sent','адитивні','gold_total, gold_hit','адитивні (чисельник/знаменник)'],
['**accuracy, faithfulness, context recall** (не зберігаються)','**неадитивні** (частки): лише SUM/SUM, не AVG','напівадитивних немає','немає балансів/знімків']],[5.2,4.3,4.0,4.5])
H('5. Перевірка: 5 запитів (sql/queries.sql; результати на 88 рядках)')
T([['BQ','Результат (фрагмент)'],
['1','accuracy = 100% у всіх групах, крім no_answer: A 87,5% (7/8), SR11 75% (3/4), B 100% (8/8)'],
['2','середня затримка пошуку (reader): A 28,0 мс → B 13,4 мс; вхідні токени A 2501 → B 2343. SR11 (1824 мс) не порівнювати: інше середовище/холодний старт'],
['3','context recall (SUM/SUM): answerable A=B 0,96 (24/25), SR11 0,80 (8/10); conflict і unsafe 1,00; uk-питання (SR11) 2/2'],
['4','faithfulness: A 0,989 (89/90), B 0,978 (90/92), SR11 1,000 (54/54); невалідних цитат 0; речень без цитат A 23, B 38, SR11 25'],
['5','помилок усього 2, обидві: NO_ANSWER → ANSWER, роль reader (A: T24, SR11: 1 питання)']],[1.0,16.9])
H('6. Генеративний ШІ: схема LLM і 3 вади (виправлено)')
P('LLM (claude-haiku-4-5, «сліпий» субагент без доступу до моїх файлів; запит: опис процесу + 5 питань + «запропонуй зіркову схему з DDL для DuckDB») запропонував схему, що виконується без помилок (llm_proposal.md). Я перевірив її на DuckDB 2.0.0 (flaws_demo.py) і знайшов:')
T([['#','Вада (тип)','Доказ','Виправлення'],
['1','**Зерно:** UNIQUE(run, test, **role**) — роль у зерні','два рядки для одного питання в одному прогоні прийнято, count = 2 → завищує знаменники accuracy','PK(run_key, test_key); роль — звичайний FK-атрибут'],
['2','**Ключі:** SCD2 зі збереженими valid_to/is_current','дві «поточні» версії та перекриття періодів прийнято. Застереження LLM, що UPDATE зламає FK, у DuckDB 2.0.0 не підтвердилось для неключових полів','зберігати лише valid_from, valid_to/is_current — view (LEAD); UNIQUE(suite,test_id,valid_from); suite у ключі (T01 не унікальний між наборами)'],
['3','**Адитивність:** зберігає context_recall та is_status_match','AVG(рядкових часток) ≠ SUM/SUM: A 0,980 проти 0,972; SR11 0,923 проти 0,895. is_status_match=1 при expected≠actual прийнято','зберігати gold_hit/gold_total; is_match — generated-стовпець у dim_outcome']],[0.6,4.4,7.4,5.5])
P('**Декларація використання ШІ.** Модель: claude-haiku-4-5 (схема-пропозиція; ідентифікатор налаштований, фактична модель могла відрізнятися) та claude-sonnet-5-5 (асистент, що написав DDL, ETL, запити і звіт). Мета: чернетка схеми, код, текст. Приклад запиту: «Запропонуй зіркову схему для оцінювання RAG-відповідей: зерно, таблиці, адитивність, ієрархії, SCD, DDL (DuckDB)». Перевірка: DDL виконано в DuckDB, 5 запитів запущено, завантажено 88 рядків факту, що збігається з кількістю у вихідних JSON (assert у build_dw.py на узгодженість gold). **Обмеження:** вибірка мала (88 рядків); перевірку «людиною» вад виконав ШІ — студент має самостійно її повторити (python3 flaws_demo.py); група категорій (answerable/unsafe) — моє рішення; мову питань визначено за кирилицею; SCD2-демо гіпотетичне (T24).',size=8)
d.add_page_break()
P('Діаграма зіркової схеми (src: out/star.mmd)',True,10)
d.add_picture('out/star_schema.png',width=Cm(18))
d.save('out/SR12_report.docx')
