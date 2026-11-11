import json
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
T=json.load(open('../situation_templates.json'))
d=Document(); s=d.sections[0]; s.page_width=Cm(21); s.page_height=Cm(29.7)
for a in ('left_margin','right_margin'): setattr(s,a,Cm(1.6))
s.top_margin=Cm(1.3); s.bottom_margin=Cm(1.2)
st=d.styles['Normal']; st.font.name='Calibri'; st.font.size=Pt(8.5); st.element.rPr.rFonts.set(qn('w:eastAsia'),'Calibri')
st.paragraph_format.space_after=Pt(2); st.paragraph_format.space_before=Pt(0)
def P(t,b=False,sz=None,al=None):
    p=d.add_paragraph(); r=p.add_run(t); r.bold=b
    if sz: r.font.size=Pt(sz)
    if al: p.alignment=al
    return p
def H(t): 
    p=P(t,True,10); p.paragraph_format.space_before=Pt(4); return p
def shade(c):
    tcPr=c._tc.get_or_add_tcPr(); sh=OxmlElement('w:shd'); sh.set(qn('w:val'),'clear'); sh.set(qn('w:fill'),'D9E2F3'); tcPr.append(sh)
def tab(head,rows,w):
    t=d.add_table(rows=1,cols=len(head)); t.style='Table Grid'; t.autofit=False
    for i,h in enumerate(head):
        c=t.rows[0].cells[i]; c.text=''; r=c.paragraphs[0].add_run(h); r.bold=True; r.font.size=Pt(8); shade(c)
    for row in rows:
        cs=t.add_row().cells
        for i,v in enumerate(row):
            cs[i].text=''; r=cs[i].paragraphs[0].add_run(str(v)); r.font.size=Pt(8)
    for i,x in enumerate(w): t.columns[i].width=Cm(x)
    for row in t.rows:
        for i,x in enumerate(w): row.cells[i].width=Cm(x)
        for c in row.cells:
            for p in c.paragraphs: p.paragraph_format.space_after=Pt(0)
P('Самостійна робота 7. Помилки в онтологіях та шаблони ситуацій',True,13,WD_ALIGN_PARAGRAPH.CENTER)
P('Курс «Сховища знань та управління знаннями» · Предметна область: медицина · Онтологія: OGMS (Ontology for General Medical Science)',al=WD_ALIGN_PARAGRAPH.CENTER)
H('1. Вхід і методика')
P('Онтологія: знімок OGMS (версія 2011, репозиторій biolisp/ogms), RDF/XML — 81 власний клас OGMS (96 класів у робочому файлі разом із заглушкою BFO/IAO), лише ієрархія is-a, без властивостей і обмежень. Поточна версія ogms.owl на GitHub є заглушкою на 17 класів, тому використано знімок; частина дефектів у нових версіях може бути вже усунена. '
  'Інструменти: (1) reasoner HermiT (owlready2) — узгодженість і незадовільні класи; (2) власний скрипт OOPS!-подібних перевірок (pitfalls.py; сервіс OOPS! був недоступний — це НЕ результат OOPS!); (3) спрощена перевірка OntoClean за теґами, призначеними мною вручну; (4) слабкий «сліпий» LLM-рецензент без інструментів. '
  'Оскільки імпорт BFO недоступний офлайн, я додав мінімальну заглушку BFO зі спогаду (13 класів, 5 пар дизʼюнктності) — вона дає reasoner-у базову дизʼюнктність; це не оригінальний BFO.')
H('2. Знайдені проблеми (16 у xlsx; ключові)')
tab(['ID','Класи','Проблема','Тип','Виявлено'],[
('D1','pain ⊑ symptom','процес під анти-ригідною роллю','логіка/OntoClean','вручну, LLM'),
('D2','disease stage ⊑ disease course','стадія — частина перебігу, не підклас; relapse/remission стають «перебігами»','логіка/OntoClean','вручну, LLM, HermiT'),
('D3','normal/abnormal homeostasis, chronic/transient course та ін.','немає жодної аксіоми дизʼюнктності','логіка','скрипт P10, LLM'),
('D4','sign, symptom','визначення «якість АБО процес» під entity','OntoClean (єдність)','вручну, LLM'),
('D5','4 примітиви (physical basis, realization…)','відношення змодельовані як класи без визначень','логіка','вручну, LLM'),
('D6/D7','8 класів «TODO», 7 без визначення','неповна документація','документація','скрипт P08, LLM'),
('D8–D11','мітка з пробілом, «_», «data itme», «an spatial», IRI .owl#','іменування/метадані','іменування','скрипт, LLM'),
('D12','заголовок','немає ліцензії (P41)','документація','скрипт'),
('D13','treatment, disease prophylaxis','за визначенням мають бути під health care process','логіка','LLM (перевірено)'),
],[1.2,4.6,6.2,2.8,2.9])
P('Базовий результат HermiT: онтологія узгоджена, 0 незадовільних класів — тобто reasoner не виявив жодної з цих проблем. Усі вони «тихі»: відсутні аксіоми й хибні is-a не створюють суперечності.')
H('3. Виправлення та ефект на виведення (HermiT, до → після)')
tab(['Виправлення','Ефект (до → після)'],[
('A. Дизʼюнктність 4 пар (normal/abnormal homeostasis; chronic/transient course; inpatient/outpatient; health care process/ancillary)','Тестові проби-перетини: задовільні (0 з 4) → незадовільні (4 з 4); індивід «chronic+transient»: consistent → INCONSISTENT. Відповідно P10: 15 → 12 груп без дизʼюнктності. (Пара disease⟂disorder вже виводилась із заглушки BFO — не нова.)'),
('B. disease stage: прибрано is-a disease course, додано is-a process та part_of some disease course','relapse ⊑ disease course: так → ні; remission ⊑ disease course: так → ні; OntoClean: порушення єдності усунено.'),
('C. pain: під bodily process замість symptom','pain ⊑ occurrent: ні → так; pain ⊑ symptom: так → ні; проба pain⊓quality: задовільна → незадовільна; порушення ригідності усунено.'),
('D. Іменування: пробіл, «_», typo ×2, IRI','Pitfall P22: 3 → 1; P36: 1 → 0; typo: 2 → 0. IRI замінено тимчасовим локальним OGMS_9000001 (не офіційний ID).'),
],[7.0,10.7])
P('Результат після виправлень: незадовільних проб 6 з 6 (з них P5 disease⊓disorder — і до змін), порушень OntoClean 0 (за моїми теґами). Пробні класи/індивід додаються лише в памʼять і не входять у ogms_fixed.owl.')
H('4. П’ять шаблонів ситуацій (стан → подія → умова → новий стан → дія)')
tab(['#','Стан → Подія → Умова','→ Новий стан · Дія','Класи онтології'],[(t['id'],f"{t['name']}. {t['state']} → {t['event']} → {t['condition']}",f"{t['new_state']} · {t['action']}",', '.join(t['classes'])) for t in T],[0.8,6.8,5.2,4.9])
P('Усі 35 посилань на класи перевірено скриптом (templates.py) за мітками в ogms_fixed.owl. Шаблони корисні тим, що відділяють подієву логіку від таксономії: правило формулюється лише в термінах класів онтології, тож його можна перевіряти й повторно використовувати; клінічну коректність порогів і умов мають підтвердити лікарі.')
H('5. LLM-рецензент проти інструментів')
P('Рецензент (Sonnet, без доступу до інструментів, отримав перелік «клас ⊑ батьки :: визначення») дав 12 груп знахідок. Збіг із моїми/скриптовими: примітиви, TODO, pain/sign/symptom, stage vs course, дизʼюнктність, typo. Нове й підтверджене за переліком: D13 (treatment під planned process), D14, D16. '
  'Помилки: (1) п.8 — «анти-ригідний клас як підклас» подано як OntoClean-порушення, хоча анти-ригідний підклас під ригідним допустимий (реальна проблема — відсутня дизʼюнктність); (2) п.6 — «hospitalization і inpatient — синоніми» без підстав (визначень немає, TODO); (3) нарікання на «обрізані визначення» — артефакт мого скорочення переліку; (4) не міг побачити IRI, ліцензію та поведінку reasoner. Дрібна: LLM не відрізняє підтверджене reasoner-ом від припущення.')
H('6. Відповіді на самоперевірку')
P('1) Типові помилки з ролями: роль (анти-ригідна) стає батьком ригідного типу (pain ⊑ symptom); роль змодельована як підклас замість зв’язку; змішування ролі та виду в одній ієрархії. '
  '2) Reasoner виявляє суперечності й незадовільні класи лише за наявних аксіом; не бачить відсутніх аксіом, хибних але узгоджених is-a, документації та іменування — тут він дав «0 проблем». '
  '3) Шаблон ситуації фіксує повторювану клінічну подію як правило над класами, що робить онтологію придатною для керування та перевірки. '
  '4) LLM-рецензент помилився в трактуванні ригідності, висунув спекулятивну «синонімію» і не відрізняв перевірені факти від припущень.')
H('7. Декларація використання ШІ та обмеження')
P('Модель: Claude (Anthropic). Призначення: допомога в написанні скриптів, підготовці звіту та як «сліпий» LLM-рецензент. Приклад запиту: «Знайди до 12 проблем в онтології (логічні, іменування, документація, OntoClean) з класами, категорією і впевненістю». Перевірка: знахідки звірено з переліком класів і скриптами; reasoner запущено локально; помилки рецензента зафіксовано вище. '
  'Обмеження: OOPS! не запускався; BFO — заглушка зі спогаду; OntoClean-теги мої, не формально верифіковані (після виправлення «0 порушень» залежить від них); знімок OGMS застарілий; LLM-рецензент і автор виправлень — одна модельна родина; вказані пороги й клінічні умови потребують перевірки експертом. Студент має самостійно перевірити знахідки в онтології.',)
d.save('../SR7_report.docx')
