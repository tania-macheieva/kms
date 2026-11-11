import json, pitfalls
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
ROOT=Path(__file__).resolve().parents[1]
R=json.load(open(ROOT/'reasoner_results.json',encoding='utf-8')); O=json.load(open(ROOT/'ontoclean_results.json',encoding='utf-8')); T=json.load(open(ROOT/'situation_templates.json',encoding='utf-8'))
P=[ # id, класи, проблема, категорія, виявлено, серйозність, статус
('D1','pain, symptom','pain (процес за визначенням) ⊑ symptom (анти-ригідна роль); в онтології pain не виводиться як occurrent','логічна + OntoClean (ригідність)','вручну; LLM; OntoClean-скрипт','висока','виправлено (C)'),
('D2','disease stage, disease course, relapse, remission','стадія — частина перебігу, але змодельована як is-a; не успадковано критерій єдності; relapse/remission стають «перебігами»','логічна + OntoClean (єдність)','вручну; LLM; OntoClean-скрипт; HermiT (вивід)','висока','виправлено (B)'),
('D3','normal/abnormal homeostasis; chronic/transient course; inpatient/outpatient; health care process/ancillary','відсутні аксіоми дизʼюнктності (у знімку їх немає взагалі); суперечливі проби виводяться як задовільні','логічна','pitfall P10; HermiT-проби; LLM','висока','виправлено (A)'),
('D4','sign, symptom','диз’юнктивне визначення (якість АБО процес) під entity','логічна + OntoClean (єдність)','вручну; LLM','висока','відкрито'),
('D5','undefined primitive term, physical basis, realization, clinically abnormal','відношення/предикат змодельовані як класи, без визначень','логічна (мета-рівень)','вручну; pitfall P08a; LLM','середня','частково (перейменовано)'),
('D6','8 класів (ED/inpatient/outpatient encounter, hospitalization, pathological formation/invasion, portion of pathological body substance, physical examination finding)','визначення «TODO»','документація','pitfall P08b; LLM','середня','відкрито'),
('D7','bodily process, homeostasis, disease stage (+4 примітиви)','немає визначення','документація','pitfall P08a; LLM','середня','відкрито'),
('D8','health care process biomaterial transformation','пробіл наприкінці мітки','іменування','pitfall P22; LLM','низька','виправлено (D)'),
('D9','undefined primitive term','мітка починається з «_»; ED encounter — абревіатура','іменування','pitfall P22; LLM','низька','частково (D)'),
('D10','laboratory test, configuration','друкарські помилки «data itme», «an spatial»','документація','pitfall TYPO; вручну (itme); LLM (an spatial)','низька','виправлено (D)'),
('D11','disease stage','IRI ogms.owl#disease_stage (розширення файлу, не OBO-стиль)','іменування/метадані (P36)','pitfall P36','низька','виправлено (D, тимчасовий ID)'),
('D12','ontology header','немає ліцензії','документація (P41)','pitfall P41','низька','відкрито (рішення авторів)'),
('D13','treatment, disease prophylaxis, health care process','за визначенням health care process вони мають бути його підкласами, але стоять під planned process','логічна','LLM; перевірено за переліком','середня','відкрито (потрібен експерт)'),
('D14','disease phenotype, clinical phenotype','disease phenotype за визначенням — клінічний фенотип, але сестра, а не дочірній клас','логічна','LLM; перевірено за переліком','низька','відкрито'),
('D15','vital sign, laboratory test','у визначеннях згадано «physical sign» / «measurement assay» — таких класів немає','документація','вручну; LLM','низька','відкрито'),
('D16','syndrome, manifestation of a disease','«патерн ознак» як quality — сумнівна єдність','OntoClean (єдність)','вручну; LLM','низька','відкрито'),
]
wb=Workbook(); H=Font(bold=True,color='FFFFFF'); F=PatternFill('solid',fgColor='305496'); W=Alignment(wrap_text=True,vertical='top')
def sheet(name,head,rows,widths):
    ws=wb.create_sheet(name); ws.append(head)
    for c in ws[1]: c.font=H; c.fill=F; c.alignment=W
    for r in rows: ws.append(list(r))
    for i,w in enumerate(widths,1): ws.column_dimensions[get_column_letter(i)].width=w
    for row in ws.iter_rows(min_row=2):
        for c in row: c.alignment=W
    ws.freeze_panes='A2'; return ws
wb.remove(wb.active)
sheet('1_Проблеми',['ID','Класи','Проблема','Категорія','Як виявлено','Серйозність','Статус'],P,[6,38,60,26,32,12,24])
rows=[]
for k in R['before']['unsat_probes']: rows.append((k,'так' if R['before']['unsat_probes'][k] else 'ні','так' if R['after']['unsat_probes'][k] else 'ні'))
for k in ['relapse ⊑ disease course','remission ⊑ disease course','pain ⊑ occurrent','pain ⊑ symptom','individual chronic+transient','n_unsat_total']:
    rows.append((k+(' (проби, окрім Nothing)' if k=='n_unsat_total' else ''),str(R['before'][k]),str(R['after'][k])))
rows.append(('предки pain','; '.join(R['before']['ancestors(pain)']),'; '.join(R['after']['ancestors(pain)'])))
rows.append(('предки relapse','; '.join(R['before']['ancestors(relapse)']),'; '.join(R['after']['ancestors(relapse)'])))
rows.append(('час HermiT, с',R['before']['time_s'],R['after']['time_s']))
sheet('2_Reasoner',['Перевірка (проба = додатковий тестовий клас, лише в памʼяті)','До виправлень (клас unsat?)','Після'],rows,[62,50,50])
n0,b=pitfalls.run(str(ROOT/'ogms_work.owl')); n1,a=pitfalls.run(str(ROOT/'ogms_fixed.owl'))
sheet('3_Pitfalls',['OOPS!-подібна перевірка (власний скрипт, не сервіс OOPS!)','До','Після','Приклади (до)'],[(k,len(b[k]),len(a[k]),'; '.join(b[k][:6])) for k in b],[50,8,8,80])
oc=[(c,p,m,'порушення') for c,p,m in O['before']['violations']]+[(c,p,m,'порушення усунено') for c,p,m in O['before']['violations'] if not any(x[0]==c for x in O['after']['violations'])][:0]
rows=[(c,p,m,'до виправлень') for c,p,m in O['before']['violations']]+[(c,p,m,'після виправлень') for c,p,m in O['after']['violations']]
rows.append(('(перевірено ребер без порушень)','',f"до: {O['before']['ok_edges']}; після: {O['after']['ok_edges']}",''))
sheet('4_OntoClean',['Підклас','Батько','Порушення','Стан'],rows,[28,28,80,18])
sheet('5_Теги OntoClean',['Клас','Ригідність','Критерій єдності (авторський)'],[(k,v[0],v[1] or '—') for k,v in O['tags'].items()],[34,12,60])
L=[
('1 примітиви-класи','так (D5)','підтверджено'),('2 TODO/без визначень','так (D6,D7)','підтверджено скриптом'),
('3 sign/symptom/pain','так (D1,D4)','підтверджено'),('4 stage is-a course','так (D2)','підтверджено; HermiT показує вивід relapse⊑course'),
('5 treatment під planned process','нове (D13)','підтверджено за переліком; потрібен експерт'),('6 hospitalization = inpatient (синоніми)','спекуляція','НЕ підтверджено: визначень немає (TODO)'),
('7 патологічні сутності не під disorder; inflammatory process','частково','спірно: залежить від задуму авторів'),('8 normal/abnormal «анти-ригідні як підклас»','ні (D3 — інше)','ПОМИЛКА LLM: за OntoClean анти-ригідний підклас під ригідним допустимий; реальна проблема — відсутня дизʼюнктність'),
('9 генетичні розлади без дизʼюнктності','так (D3-тип)','підтверджено (pitfall P10)'),('10 disease phenotype / syndrome','нове (D14,D16)','підтверджено за переліком'),
('11 clinical finding / preclinical finding / normal value','частково','правдоподібно, не перевірялось з експертом'),('12 іменування, typo','так (D8–D10,D15)','підтверджено; «обрізані визначення» — артефакт МОГО переліку (я скоротив тексти), не онтології'),
('Чого LLM не міг побачити','IRI .owl#, ліцензія, результат reasoner','перелік без IRI/метаданих; reasoner недоступний'),
]
sheet('6_LLM vs інструменти',['Знахідка LLM-рецензента','Збіг з моїм списком','Висновок'],L,[48,26,80])
sheet('7_Шаблони ситуацій',['ID','Назва','Стан','Подія','Умова','Новий стан','Дія','Звʼязані класи'],[(t['id'],t['name'],t['state'],t['event'],t['condition'],t['new_state'],t['action'],'; '.join(t['classes'])) for t in T],[5,30,36,36,32,36,40,60])
wb.save(ROOT/'SR7_ontology_errors.xlsx'); print('ok',n0,n1)
