import json
from docx import Document
from docx.shared import Pt,Cm,RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
M=json.load(open('metrics.json')); ML=json.load(open('metrics_lemma.json')); CI=json.load(open('ci.json'))
R=json.load(open('rules_out.json')); SP=json.load(open('spacy_out.json'))
d=Document(); s=d.sections[0]; s.page_width=Cm(21); s.page_height=Cm(29.7)
s.left_margin=s.right_margin=Cm(1.8); s.top_margin=Cm(1.2); s.bottom_margin=Cm(1.1)
st=d.styles['Normal']; st.font.name='Calibri'; st.font.size=Pt(10); st.element.rPr.rFonts.set(qn('w:eastAsia'),'Calibri')
st.paragraph_format.space_after=Pt(3)
def P(t,b=False,size=None):
    p=d.add_paragraph()
    for i,x in enumerate(t.split('**')):
        r=p.add_run(x); r.bold=b or i%2==1
        if size: r.font.size=Pt(size)
    return p
def H(t):
    p=P(t,True,12); p.paragraph_format.space_before=Pt(8); p.runs[0].font.color.rgb=RGBColor(0x1F,0x3A,0x6E)
def T(rows,w,fs=8.5):
    t=d.add_table(rows=len(rows),cols=len(w)); t.style='Table Grid'; t.autofit=False
    for i,r in enumerate(rows):
        for j,x in enumerate(r):
            c=t.cell(i,j); c.width=Cm(w[j]); p=c.paragraphs[0]; p.paragraph_format.space_after=Pt(0)
            for k,y in enumerate(str(x).split('**')):
                rr=p.add_run(y); rr.font.size=Pt(fs); rr.bold=(i==0) or k%2==1
            if i==0:
                sh=OxmlElement('w:shd'); sh.set(qn('w:val'),'clear'); sh.set(qn('w:fill'),'DCE6F5'); c._tc.get_or_add_tcPr().append(sh)
    for j,x in enumerate(w): t.columns[j].width=Cm(x)
    d.add_paragraph().paragraph_format.space_after=Pt(2)
f=lambda x:f'{x:.2f}'
P('Самостійна робота 13 — Порівняння методів витягу відношень',True,15)
P('Курс «Сховища знань та управління знаннями» · домен: медицина / біомедичні дані (документація біоінформатичних інструментів) · студент: ________ · 12.11.2026',size=9)
H('1. Набір даних і золота розмітка (C1)')
P('**50 речень** з англомовної документації, яку вже використовували у ЛР11 (bcftools, GATK/Funcotator, nf-core Sarek/RaRe): реальні речення, не вигадані. Відбір: з ~960 кандидатів (9–35 слів, без коду й посилань) випадкова вибірка (seed 13, ≤4 речень з документа); з неї залишено 39 речень із явним відношенням і додано **11 речень без жодного відношення** (перевірка хибних спрацювань). Відбір по «явному відношенню» робив я вручну — це зсув набору до речень, придатних для витягу (див. обмеження).')
P('**Схема відношень (6 предикатів):** uses (X використовує/потребує/запускає Y), produces, supports (підтримує/дозволяє/приймає), is_a, contains (містить/включає/зберігає), performs (X виконує завдання Y). Золота розмітка: **60 трійок (s,p,o)** у 39 реченнях; 11 речень — порожня розмітка (gold.json, annotation.csv). Розмічено лише явні відношення, повні референти займенників не відновлювалися (залишено «It», «This repo»).')
P('**Нормалізація перед порівнянням:** нижній регістр; прибрано `*_`, лапки, дужки, розділові знаки; відкинуто початкові артиклі/детермінативи (the, a, this, some, each…). **Strict** — збіг (s,p,o) після нормалізації; **Lenient** — предикат збігається точно, а суб’єкт і об’єкт — коли одна множина слів міститься в іншій або Jaccard ≥ 0,5 (щоб «samtools sort» ≈ «samtools»). Метрики: TP — перший непорожній збіг, кожну золоту трійку зараховано один раз; P = TP/(TP+FP), R = TP/(TP+FN), F1 — гармонічне середнє. Лематизація як чутливий аналіз (останній стовпець).')
H('2. Три методи')
T([['Метод','Що це','Налаштування'],
['Правила','~12 регулярних/позиційних шаблонів по токенах (без парсингу): лексикон дієслів → предикат; «X is a Y»; пасив «Y is used by X»; NP = до 5 слів ліворуч/6 праворуч до межі (кома, прийменник, дужка)','m_rules.py'],
['spaCy','en_core_web_sm 3.8: залежнісний розбір; для дієслів з лексикону пари nsubj–dobj (+ пасив з agent, + кон’юнкти), копула be + attr → is_a; суб’єкт/об’єкт = іменна група','m_spacy.py; той самий лексикон, що й у правил'],
['LLM зі схемою','claude-haiku-4-5 (субагент, «сліпий»: бачив лише 50 речень і схему, без золота й без інструментів); виводить JSON-трійки + поле «doubt» для сумнівних','1 запит, 50 речень, llm_out.json']],[2.6,11.4,3.4])
P('Правила й spaCy написано **один раз і не підганялось** під метрики (без dev/test-поділу, бо мало даних), але лексикон складено після перегляду речень, тож їхній результат можливо дещо завищений.',size=9)
H('3. Результати: P/R/F1 і вартість (C2)')
rows=[['Метод','n прогноз','TP / FP / FN (lenient)','P','R','F1 strict [95% ДІ]','F1 lenient [95% ДІ]','F1 lenient + лема','Вартість','Час']]
cost={'Правила':('$0','1,1 мс на 50 речень'),'spaCy':('$0 (CPU)','0,2 с на 50 речень (+0,28 с завантаж.)'),'LLM':('≈ $0,02 за 50 речень (оцінка; верхня межа $0,07)','≈ 62 с на 50 речень (1,2 с/речення)')}
for m in ['Правила','spaCy','LLM']:
    s_,l_=M[m]['strict'],M[m]['lenient']
    ci1=CI['strict|'+m]; ci2=CI['lenient|'+m]
    rows.append([m,M[m]['n_pred'],f"{l_['TP']} / {l_['FP']} / {l_['FN']}",f(l_['P']),f(l_['R']),f"**{f(s_['F1'])}** [{ci1[0]:.2f}–{ci1[1]:.2f}]",f"**{f(l_['F1'])}** [{ci2[0]:.2f}–{ci2[1]:.2f}]",f(ML[m]['F1']),cost[m][0],cost[m][1]])
T(rows,[1.5,1.1,2.0,0.9,0.9,2.4,2.4,1.4,2.6,2.4],fs=7.5)
P('P та R у таблиці — lenient. Strict: Правила P 0,50 / R 0,13; spaCy 0,38 / 0,17; LLM 0,56 / 0,58. Хибні спрацювання на 11 реченнях без відношень: правила 0, spaCy 0, LLM 2 (S17, S19). Різниця LLM − spaCy за F1: 95% ДІ (bootstrap по реченнях, 1000 повторів) [+0,18; +0,50] strict і [+0,14; +0,41] lenient — **значуща**; spaCy − правила: [−0,12; +0,16] — **незначуща**. Вартість LLM: токени субагента не розділено на вхідні/вихідні (звіт 74 150 токенів разом, з накладними), тому оцінка — ≈2,3 тис. вхідних + ≈4 тис. вихідних токенів за тарифом Haiku 4.5, який я пам’ятаю ($1/$5 за 1 млн); перевірте актуальний тариф. Це ≈ $0,4 на 1000 речень.',size=9)
pp=[['Предикат','Золото','Правила P/R','spaCy P/R','LLM P/R']]
import subprocess
E_=json.load(open('errors.json'))
from common import *
G={r['id']:r['gold'] for r in json.load(open('gold.json'))}
Pm={'Правила':R['preds'],'spaCy':SP['preds'],'LLM':{x['id']:[(t['s'],t['p'],t['o']) for t in x['triples']] for x in json.load(open('llm_out.json'))}}
for pr in ['uses','produces','supports','is_a','contains','performs']:
    row=[pr,sum(1 for v in G.values() for t in v if t[1]==pr)]
    for m in ['Правила','spaCy','LLM']:
        g={s:[t for t in v if t[1]==pr] for s,v in G.items()}; p={s:[t for t in v if t[1]==pr] for s,v in Pm[m].items()}
        r=score(p,g,match_len); row.append(f"{r['P']:.2f} / {r['R']:.2f}")
    pp.append(row)
P('**За предикатами (lenient):**',size=9); T(pp,[3,2,3.5,3.5,3.5])
H('4. Аналіз помилок (C3): по 12 типових помилок кожного методу')
def E(rows): T([['#','Реч.','Тип','Що сталося','Причина']]+rows,[0.7,1.0,1.0,7.7,6.0],fs=8)
P('**4.1 Правила**',size=10)
E([[1,'S01, S04, S24','FN','«sorted with samtools», «sorted using Sentieon’s sort utility» — відношень немає','шаблон знає лише пасив із «by»; інструментальне «with/using» не покрито'],
[2,'S06','FN','«datasources include GENCODE, dbSNP, gnomAD, COSMIC» — 0 з 4','дієслова в базовій формі («include») пропускаються, якщо перед ними немає модального — прогалина мого шаблону'],
[3,'S09','FN','«Funcotator (FUNCtional annOTATOR) is a functional annotation tool» не знайдено','дужка/розмітка обриває лівий контекст: суб’єкт порожній'],
[4,'S18','FP','(Sarek, contains, «support») замість (Sarek, supports, some functions)','лексична поліземія: «contains support for» — тригер «contains»'],
[5,'S27','FP+FN','(Varlociraptor, supports, «the usage») замість «different scenario files»','межа іменної групи на «of»: об’єкт обрізано'],
[6,'S44','FP','(candidate variants, is_a, «subset»)','«subset of research variants» обрізано на «of»'],
[7,'S48','FP','(sarek, uses, preprocessing) — золото: performs','вибір предиката: «runs» → uses, а об’єкт — завдання (неоднозначність схеми)'],
[8,'S28','FN','«…runs Funcotator … and produce a TCGA MAF» — produces пропущено','координація: друге дієслово в базовій формі після «and»'],
[9,'S41','FN','усі 3 золоті трійки','підрядне/умовне речення, довга залежність — вікно 5/6 слів не достатнє'],
[10,'S39, S34','FN','«is passed to VEP», «consolidated … into GenomicsDB» — нічого','пасив із прийменником «to/into» не покрито'],
[11,'S33, S35, S36','FN','«run on any Spark cluster», «built using Nextflow», «using Sentieon DNAscope»','прийменникові й дієприкметникові групи не є прямим додатком'],
[12,'усі','FN','recall лише 0,20: 48 із 60 золотих трійок пропущено','правила дають високу точність (0,75), але покривають лише явні SVO'] ])
P('**4.2 spaCy**',size=10)
E([[1,'S11','FP','(we, uses, the VQSR filtering tool)','займенник як суб’єкт; золото: is_a(VQSR, filtering tool)'],
[2,'S23','FP','(These files, contains, «_genome position»), (…, «_»)','розмітка markdown («_gene name_») ламає токенізацію/іменні групи'],
[3,'S24','FP','(Aligned reads, is_a, «coordinate»)','помилка розбору: «coordinate sorted» прочитано як копулу з attr'],
[4,'S32','FP+FN','суб’єкт «The Nextflow DSL2 implementation» замість «pipeline»; об’єкт обрізано до «one container»','PP-приєднання: «of this pipeline», «per process» не входять до noun chunk'],
[5,'S38','FP','(data_sources_tar_gz - Path, produces, annotations)','рядок опису параметра, а не речення; ціль «to create annotations» прочитано як SVO'],
[6,'S47','FP','(This, is_a, the image) — золото: (image, contains, GATK4)','відносне підрядне «where GATK4 resides» ігнорується'],
[7,'S49','FP','(that, contains, a mirror)','відносний займенник «that» не зведено до антецедента'],
[8,'S06','FN','з 4 золотих знайдено лише GENCODE','список із дужкою: кон’юнкти після дужки втрачено'],
[9,'S01, S04, S24','FN','інструментальне «with/using» — відношень нема','нема правила для prep-інструменту'],
[10,'S33, S35, S36, S45','FN','«using Sentieon DNAscope», «built using Nextflow», «using BBMap»','об’єкт — через prep/дієприкметник, а не dobj'],
[11,'S18, S44','FP','(Sarek, contains, support); (candidate variants, is_a, a subset)','поліземія «contains support»; «subset of» як тип'],
[12,'усі','FN','«performs» — 0 з 11; загальний recall 0,27','завдання-відношення часто виражені відіменником/пасивом, а не дієсловом з лексикону']])
P('**4.3 LLM**',size=10)
E([[1,'S01, S04, S24','FP+FN','(The aligned reads, uses, samtools) замість (samtools, performs, sorting)','пасив: інструмент змінено на «використовуваний», суб’єкт і предикат інші (LLM зазначив «doubt»)'],
[2,'S25','FP+FN','(REViewer, supports, The files generated) — золото uses','вибір предиката при пасиві «ready to be used with»'],
[3,'S11','FP','(we, uses, the VQSR filtering tool)','займенник «we» прийнято як суб’єкт; is_a(VQSR…) пропущено'],
[4,'S17, S19','FP','(raw data, supports, a specific allele); (Spark, supports, the cluster) на реченнях без золотих відношень','поліземія «support» (доказова, не програмна) і надмірна інтерпретація «run on» — єдині 2 FP на порожніх реченнях'],
[5,'S09','FP','(Funcotator, performs, somatic and germline use cases)','надмірне витягування зі слабкого «designed to handle» (LLM сам позначив doubt)'],
[6,'S30, S49','FP+FN','(Variant Context File, contains, variants); (an open AWS registry resource, contains, mirror…)','підміна суб’єкта типом/апозитивом замість названої сутності'],
[7,'S27, S36, S42, S44','FP*','(catalog, contains, examples); (Nextflow, supports, multiple infrastructures); (UCSC, produces, Gencode); (candidate variants, is_a, subset)','*правдоподібні за змістом, але відсутні в моєму золоті — прогалина розмітки (≈7 із 23 lenient-FP за моєю суб’єктивною оцінкою), а не помилка моделі'],
[8,'S07, S45','FP (lenient)','«summarize analysis results» vs «summarizing …», «bins reads» vs «binning reads»','нормалізація без лематизації; з лематизацією збігаються (F1 0,65→0,68)'],
[9,'S41','FP+FN','(candidate indels from Manta, uses, Strelka Best Practices); 3 золоті пропущено','умовне складне речення: суб’єкт/об’єкт переплутано'],
[10,'S34, S39','FN','«consolidated into GenomicsDB», «passed to VEP»','пасив із прийменником: відношення не оформлено'],
[11,'S40, S47','FN','(Funcotator, uses, set of data sources); (image, contains, GATK4)','відношення в підрядному «based on», «where … resides»'],
[12,'performs','FP+FN','precision 0,44 / recall 0,36 — найгірший предикат у LLM','межа «завдання» нечітка: «bins reads» ↔ «binning reads», дієслівна група замість іменної']])
H('5. Висновок і рекомендація (C4)')
P('**На цьому наборі LLM найкращий за якістю:** F1 0,57 (strict) / 0,65 (lenient) проти 0,21/0,32 (правила) і 0,23/0,37 (spaCy), відрив від spaCy статистично значущий; spaCy і правила між собою не розрізнюються (ДІ перетинають 0). Ціна — ≈ $0,4 на 1000 речень і ≈ 1,2 с на речення проти $0 і мілісекунд. **Рекомендація:** (1) для побудови графа знань із документації брати LLM як основний екстрактор, але з обов’язковою перевіркою людиною (precision лише 0,64 lenient; 2 з 11 порожніх речень дали хибні відношення), використовуючи його поле «doubt» для пріоритезації перевірки; (2) правила лишати для вузьких, стабільних шаблонів (is_a / contains / uses мають precision ≈ 0,75, нуль FP на порожніх реченнях), де потрібні детермінізм і нульова вартість; (3) spaCy у такому вигляді (SVO за залежностями) не виправдовує себе: recall 0,27 — він не покриває пасив, прийменникові групи й списки. Висновки обмежені малим набором і розміткою однією особою (див. нижче).')
H('6. Самоперевірка')
P('**1. Чому на однаковому наборі?** Інакше різниця метрик змішує якість методу зі складністю речень; на тих самих 50 реченнях і золоті порівняння парне (я використав парний bootstrap по реченнях). **2. Нормалізація** потрібна, бо «The aligned reads», «aligned reads», «`samtools sort`» — одна сутність, але різні рядки; без неї P/R занижено штучними розбіжностями регістру, артиклів і розмітки (а без лематизації «bins»≠«binning»). **3. Де LLM помилявся найчастіше?** На пасивах та інструментальних конструкціях («sorted with samtools» → хибний суб’єкт/предикат), на поліземії «support», на підміні названої сутності типом, на надмірному витягуванні додаткових фактів і найгірше на предикаті performs. **4. Коли правила кращі?** Коли конструкції вузькі й повторювані (is_a, «contains», «uses X»), потрібні нульова вартість, швидкість і відтворюваність, а також коли хибні спрацювання дорожчі за пропуски: на порожніх реченнях правила дали 0 FP при precision 0,75.')
H('7. Декларація використання ШІ та обмеження')
P('**Моделі:** claude-haiku-4-5 (налаштований ідентифікатор субагента; фактична модель могла відрізнятися) — як один із 3 методів (екстрактор); claude-sonnet-5-5 — асистент, який відібрав речення, розмітив золото, написав код методів, метрики й текст. **Приклад запиту до LLM-методу:** «Extract subject–predicate–object triples using ONLY this closed set of predicates: uses, produces, supports, is_a, contains, performs … if unsure set “doubt” to a one-line reason» (+50 речень; без золота). **Як перевірено:** метрики пораховано кодом (evaluate.py) на збережених JSON; результати LLM збережено без правок (llm_out.json); помилки класифіковано за списком FP/FN (errors.json).')
P('**Чесні обмеження:** (а) за умовою розмітку золота має виконувати людина — **її виконав ШІ**, тож золото потрібно перевірити вам (annotation.csv; змініть gold.json і запустіть evaluate.py — метрики перерахуються); (б) золото розмічено моделлю тієї ж родини, що й LLM-метод, і я знав схему — можливий зсув на користь LLM; (в) розмічено лише основні явні відношення — частина «FP» LLM є правдоподібними (прогалина розмітки); (г) відбір речень ручний (39 «з відношенням» + 11 порожніх) завищує recall усіх методів порівняно з довільним текстом; (д) 50 речень і одна розмітка — широкі довірчі інтервали; коефіцієнта узгодженості розміток немає; (е) вартість LLM — оцінка, а не виміряні токени; час включає запуск субагента; (ж) правила й spaCy не налаштовувались під метрики, але лексикон складено після перегляду речень.',size=9)
d.save('SR13_report.docx')
