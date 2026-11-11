import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
O=json.load(open('metrics.json')); rows=json.load(open('terms_table.json'))
M,C,S=O['manual'],O['cluster'],O['so']; G=O['generic']
# ---------- XLSX
wb=Workbook(); ws=wb.active; ws.title="Терміни"
hdr=["SO id","Термін","Визначення (SO, скорочено)","SO L1 (ref)","SO L2 (ref, перший батько)","Ручна L1","Ручна L2","Кластер L1","Кластер L2","Кілька батьків у SO"]
ws.append(hdr)
for r in rows: ws.append(list(r))
ws2=wb.create_sheet("Метрики")
mets=[("Метрика","Ручна (зверху вниз)","Кластеризація (знизу вгору)","SO (еталон, індукована)"),
("Термінів (покриття 100 %)",106,106,106),
("Частка «Інше», %",M['other_pct'],C['other_pct'],"—"),
("Рівнів / макс. глибина",2,2,S['max_depth']),
("Кількість груп L1",M['n_L1'],C['n_L1'],S['n_L1']),
("Кількість груп L2",M['n_L2'],C['n_L2'],S['n_L2']),
("Найбільша група L1, % термінів",M['max_L1_share'],C['max_L1_share'],round(100*61/106,1)),
("Розмір клітинки L2: мін–макс",f"{M['min_L2']}–{M['max_L2']}",f"{C['min_L2']}–{C['max_L2']}","—"),
("Одиничні клітинки L2",M['singleton_L2'],C['singleton_L2'],"—"),
("MECE: неоднозначні розміщення (поріг 0,9)",M['ambiguous_09'],C['ambiguous_09'],"—"),
("  те саме, поріг 0,8 / 1,0",f"{M['ambiguous_08']} / {M['ambiguous_10']}",f"{C['ambiguous_08']} / {C['ambiguous_10']}","—"),
("is-a пар «родовий+видовий» в одній клітинці L2 (з 109)",G['manual']['is_a_pairs_same_L2'],G['cluster']['is_a_pairs_same_L2'],"—"),
("Родові терміни, чиї нащадки розкидані по ≥2 групах L1",G['manual']['n_generic_spanning'],G['cluster']['n_generic_spanning'],"—"),
("Багатобатьківські терміни SO, чий is-a розірвано (з 14)",O['multi_lost_manual'],O['multi_lost_cluster'],"—"),
("Збіг з SO: ARI L1",M['ARI_L1'],C['ARI_L1'],1.0),
("Збіг з SO: NMI L1",M['NMI_L1'],C['NMI_L1'],1.0),
("Збіг з SO: ARI L1 (альт. батько)",M['ARI_L1_altparent'],C['ARI_L1_altparent'],1.0),
("Збіг з SO: NMI L2",M['NMI_L2'],C['NMI_L2'],1.0),
("Збіг з SO: парна F1 L2",M['pairF1_L2'],C['pairF1_L2'],1.0),
("Збереження дуг SO в межах L1 (частка)",M['edge_pres_L1'],C['edge_pres_L1'],1.0),
("NMD-терміни (8) відокремлені від базового терміна, L1",0,O['nmd']['sep_cluster_L1'],"—"),
]
for r in mets: ws2.append(list(r))
ws3=wb.create_sheet("Чутливість"); ws3.append(["k (кількість груп L1, Ward)","ARI vs SO L1","NMI vs SO L1"])
for s in O['sensitivity']: ws3.append([s['k'],s['ARI'],s['NMI']])
ws3.append([]); ws3.append(["Зв'язування","Silhouette (косинус, k=7)","Розміри кластерів"])
for k,v in O['linkage'].items(): ws3.append([k,v['silhouette'],str(v['sizes'])])
ws3.append(["Обрано (за silhouette, без звернення до SO):",O['best_linkage']])
for w in (ws,ws2,ws3):
    for c in w[1]: c.font=Font(bold=True); c.fill=PatternFill("solid",fgColor="D9E2F3"); c.alignment=Alignment(wrap_text=True,vertical="top")
for col,wd in zip("ABCDEFGHIJ",(13,42,60,26,30,28,30,34,36,12)): ws.column_dimensions[col].width=wd
for col,wd in zip("ABCD",(58,24,28,24)): ws2.column_dimensions[col].width=wd
ws3.column_dimensions['A'].width=44; ws3.column_dimensions['B'].width=28; ws3.column_dimensions['C'].width=24
DEF=[
("1","Велика «Інше»",f"«Інше»: 7 термінів, {M['other_pct']} % (NMD_transcript_variant, coding_transcript_variant, complex_…, intragenic_…, три *_duplicated_transcript) — різнорідний залишок без спільної ознаки.","Метрика «Інше»; LLM-зауваження 9 (підтверджено)","Розкласти: дублікати транскриптів → окрема група «Структура транскрипта»; цільовий поріг «Інше» ≤ 5 %."),
("2","Змішані принципи поділу на L1",f"L1 — це ділянка (CDS, сплайсинг, UTR, інтрони/екзони), але «Некодувальні РНК» — тип РНК, «Неповні транскрипти» — статус анотації. Неоднозначних розміщень: {M['ambiguous_09']} у ручній ({', '.join(O['amb_manual'][:3])}…).","LLM-зауваження 1, 4 (підтверджено); метрика неоднозначності","Розділити на фасети: ділянка × ефект × тип/статус транскрипта (окремі схеми SKOS)."),
("3","Родовий і видові терміни в одній клітинці",f"{G['manual']['is_a_pairs_same_L2']} із 109 пар is-a SO опинилися в одній клітинці L2 ручної (напр. start_lost ⊂ initiator_codon_variant, stop_lost ⊂ terminator_codon_variant). Узагальнення стоїть поруч із конкретикою без вказівки на підпорядкування.","LLM-зауваження 5 (підтверджено, перевірено за is_a SO)","Родові терміни зробити батьківськими вузлами (broader), не листками; метрика → 0."),
("4","Хибно розміщений родовий термін",f"coding_sequence_variant стоїть у «CDS: зміна амінокислоти», але в SO має 39 нащадків (synonymous, frameshift, stop_gained, start_lost…). Так само splicing_variant у «нових сайтах».","LLM-зауваження 5а, 8 (підтверджено частково: exon_loss/intron_gain/pseudoexon у SO справді під splicing_variant)","Підняти родові терміни на рівень батьківської групи."),
("5","Втрата багатобатьківських зв'язків",f"{O['multi_lost_manual']} із 14 термінів SO з ≥2 батьками в межах множини мають батьків у різних групах L1 ручної таксономії (кластерної — {O['multi_lost_cluster']}), напр. stop_retained_variant ⊂ terminator_codon_variant і ⊂ synonymous_variant; дерево зберігає лише один зв'язок.","метрика multi_lost; перевірено за is_a SO","Дозволити skos:broader з кількома значеннями або винести як фасет."),
("6","Ортогональна вісь NMD",f"8 термінів *_NMD_escaping/triggering. Ручна розкидає їх за базовим терміном (у двох групах L1: CDS і сплайсинг), кластеризація збирає всіх у один кластер із NMD_transcript_variant (чистота за SO лише 0,44). Жодне дерево не передає обидві осі.","LLM-зауваження 10 (підтверджено); кластер C2","Окремий фасет «Доля транскрипта (NMD)»; кластеризація виявила його без підказки."),
("7","Зливний кластер у кластеризації",f"Кластер C7: 32 терміни, чистота за SO 0,41 (9 груп SO), токени «coding, transcript, inframe» — текстова подібність не відображає біологічну; max L1 = {C['max_L1_share']} %.","cluster_info","Використовувати кластеризацію лише для пропозицій кандидатів груп; рівень L1 затверджує експерт."),
]
ws4=wb.create_sheet("Дефекти"); ws4.append(["№","Дефект","Що знайдено","Як виявлено/перевірено","Виправлення"])
for r in DEF: ws4.append(list(r))
for c in ws4[1]: c.font=Font(bold=True); c.fill=PatternFill("solid",fgColor="D9E2F3")
for col,wd in zip("ABCDE",(5,30,80,42,50)): ws4.column_dimensions[col].width=wd
for row in ws4.iter_rows(min_row=2):
    for c in row: c.alignment=Alignment(wrap_text=True,vertical="top")
LLM=[("1","Змішування принципів на L1","висока","Підтверджено"),("2","Сплайсинг ⊂ інтрони/екзони","висока","Частково: splice_site/acceptor/donor справді нащадки intron_variant в SO; твердження про exon_variant не підтверджено (splice_acceptor не в exon_variant)"),
("3","Старт/стоп vs без зміни vs зсув рамки","висока","Частково: stop_retained має двох батьків (terminator_codon, synonymous) — правда; «stop_gained = frameshift_truncation» і «NMD-терміни перетинаються» — хибно, різні батьки"),
("4","Різні вісі на L2","висока","Підтверджено"),("5","Родові й видові терміни поруч","висока","Підтверджено (start_lost ⊂ initiator_codon_variant, stop_lost ⊂ terminator_codon_variant)"),
("5а","coding_sequence_variant у «зміні амінокислоти»","висока","Підтверджено (39 нащадків у SO)"),("6","rare_amino_acid/selenocysteine ближчі до стоп-кодона","середня","Відхилено: у SO rare_amino_acid_variant ⊂ non_conservative_missense_variant, визначення — зміна амінокислоти; аргумент про рекодування стоп-кодона не випливає з даних"),
("7","5' передчасний старт перетинається з uORF","середня","Частково: у SO це сусідні нащадки 5_prime_UTR_variant, семантичне перекриття правдоподібне, але не перевірене; асиметрія 5'/3' — факт, не порушення MECE"),
("8","exon_loss/intron_gain/pseudoexon не «сайти»","середня","Частково: у SO вони під splicing_variant (розміщення коректне); але сам splicing_variant — родовий і стоїть не там"),
("9","«Інше» і «Неповні транскрипти» змішані","висока","Підтверджено"),("10","NMD як ортогональна вісь; miRNA vs структура","середня","Частково: NMD-вісь підтверджено; зауваження про miRNA відхилено (mature_miRNA_variant ⊂ non_coding_transcript_variant у SO)")]
ws5=wb.create_sheet("LLM-перевірка MECE"); ws5.append(["№ зауваження LLM","Суть","Впевненість LLM","Результат перевірки за SO"])
for r in LLM: ws5.append(list(r))
for c in ws5[1]: c.font=Font(bold=True); c.fill=PatternFill("solid",fgColor="D9E2F3")
for col,wd in zip("ABCD",(14,48,16,100)): ws5.column_dimensions[col].width=wd
for row in ws5.iter_rows(min_row=2):
    for c in row: c.alignment=Alignment(wrap_text=True,vertical="top")
wb.save('SR5_taxonomy_comparison.xlsx')
# ---------- DOCX
d=Document()
for s in d.sections: s.top_margin=s.bottom_margin=Cm(1.5); s.left_margin=Cm(1.9); s.right_margin=Cm(1.6)
d.styles['Normal'].font.name='Times New Roman'; d.styles['Normal'].font.size=Pt(10)
def p(t,b=False,al=None,sz=None):
    x=d.add_paragraph(); r=x.add_run(t); r.bold=b
    if sz: r.font.size=Pt(sz)
    if al: x.alignment=al
    x.paragraph_format.space_after=Pt(3); return x
def tbl(data,w):
    t=d.add_table(rows=len(data),cols=len(data[0])); t.style='Table Grid'; t.autofit=False
    for i,row in enumerate(data):
        for j,c in enumerate(row):
            cell=t.cell(i,j); cell.text=''; r=cell.paragraphs[0].add_run(str(c)); r.font.size=Pt(8.5); r.bold=(i==0)
            cell.paragraphs[0].paragraph_format.space_after=Pt(0)
    for j,x in enumerate(w):
        t.columns[j].width=Cm(x)
        for row in t.rows: row.cells[j].width=Cm(x)
    d.add_paragraph().paragraph_format.space_after=Pt(1)
p("Львівський національний університет імені Івана Франка · Кафедра системного проєктування",al=WD_ALIGN_PARAGRAPH.CENTER,sz=9)
p("Самостійна робота 5. Порівняння методів побудови таксономій",True,WD_ALIGN_PARAGRAPH.CENTER,14)
p("Курс «Сховища знань та управління знаннями» · Медицина / аналіз біомедичних даних · Виконав(ла): ____________ · Дата: ________",al=WD_ALIGN_PARAGRAPH.CENTER,sz=9)
p("1. Домен і методи (C1)",True,sz=12)
p("Домен — типи наслідків варіантів у транскрипті (продовження тематики СР3–СР4): 106 термінів — усі нащадки transcript_variant у Sequence Ontology (SO, версія даних 2026-08-07, so-simple.obo з GitHub The-Sequence-Ontology). "
  "Трьома таксономіями в єдиному форматі (taxonomies.json: id, label, broader за моделлю skos:broader) є: (А) ручна «зверху вниз» — 2 рівні, 7 груп L1 і 18 груп L2; принцип поділу: ділянка транскрипта → тип ефекту; "
  "(Б) кластеризація «знизу вгору» — TF-IDF за назвою й визначенням, агломеративна кластеризація; зв'язування Ward обрано за внутрішньою метрикою silhouette (0,208 проти 0,126 для average; complete не дала розбиття), без звернення до SO; число груп (7 і 18) узято таким самим, як у ручній, для рівних умов; "
  "(В) еталон — іс-а ієрархія SO (третя, зовнішня експертна таксономія). Зверніть увагу: ручну таксономію склав ШІ (див. §5), тому вона експертна за змістом, але не незалежна від моделі, що писала код.")
p("2. Метрики (C2)",True,sz=12)
rowsM=[["Метрика","Ручна","Кластеризація","SO (еталон)"]]+[list(map(str,r)) for r in mets[2:13]+mets[13:20]]
tbl(rowsM,[8.5,2.8,3.4,2.8])
p("Покриття — 100 % для обох (106 з 106). «Збіг із SO» рахується відносно L1 SO за першим батьком (у цьому розбитті 61 термін із 106 під exon_variant, тому ARI занижується для будь-якої збалансованої таксономії; для перевірки наведено NMI, альтернативний вибір батька й збіг на рівні L2). "
  "Неоднозначність: терміну, другий найближчий центроїд групи якого майже такий самий близький, як власний (поріг 0,9; при 0,8 і 1,0 висновок той самий).")
p("Висновок за метриками. Ручна таксономія значно ближча до експертної (NMI L1 0,78 проти 0,47; збережено 90 % дуг SO проти 73 %), але має «Інше» 6,6 % і 4 родові терміни з розкиданими нащадками. Кластеризація не має «Інше» і одиничних груп, "
  "проте її найбільший кластер (32 терміни, чистота за SO 0,41) змішує дев'ять груп SO; чутливість до k невелика за NMI (0,34–0,54), ARI нестабільний (0,05–0,18). За збігом із SO кластеризація поступається ручній за всіма метриками; її перевага — відсутність «Інше» і виявлення прихованої осі NMD.")
p("3. Дефекти (C3, ≥5)",True,sz=12)
tbl([["№","Дефект","Докази / перевірка"]]+[[r[0],r[1],r[2]+" ["+r[3]+"]"] for r in DEF],[0.7,3.6,13.2])
p("Перевірка зауважень LLM (кроки з §5): окремий агент Claude Sonnet 5.5 (без інструментів і без доступу до SO) отримав ручну таксономію й дав 11 зауважень; за визначеннями та is_a SO із них 5 підтверджено повністю, 5 — частково, 1 відхилено (rare_amino_acid ближчі до стоп-кодона — суперечить SO). Окремі твердження (напр. «stop_gained = frameshift_truncation») хибні й відкинуті. Деталі — аркуш «LLM-перевірка MECE».")
p("4. Рекомендації з поєднання методів (C4)",True,sz=12)
for t in ["Гібрид: кластеризація пропонує кандидати груп (вона самостійно виділила NMD-фасет і групу incomplete_transcript), а верхні рівні затверджує експерт — бо найбільший автоматичний кластер змішав дев'ять груп SO (дефект 7).",
 "Фасети замість одного дерева: ділянка × ефект × доля транскрипта (NMD) × повнота анотації, кожна вісь як окрема схема SKOS (дефекти 2, 6). Це зніме змішування принципів і втрату багатобатьківських зв'язків (дефект 5: 9 із 14 термінів).",
 "Родові терміни — лише батьківські вузли (broader), а не листки поруч із видовими: ціль «is-a пар в одній клітинці» → 0 (зараз 76 із 109), «Інше» ≤ 5 % (зараз 6,6 %).",
 "Зміни без поломки аналітики: стабільні id термінів (як SO:…), переміщення — лише зміною broader, видалення — через deprecated + replacedBy, аналітика на id, а не на назвах груп; перед змінами повторювати метрики з цього звіту."]:
    d.add_paragraph(t,style='List Bullet').paragraph_format.space_after=Pt(1)
p("5. Декларація використання ШІ",True,sz=12)
p("Модель: Claude Sonnet 5.5 (Anthropic). Призначення: завантаження й обробка SO, побудова ручної таксономії, код кластеризації й метрик, оформлення звіту; окремий екземпляр моделі (без інструментів і без SO) — «рецензент MECE». "
  "Приклад запиту: «Знайди порушення MECE у цій таксономії: назви конкретні терміни, суть порушення, свою впевненість». Перший запуск не спрацював через мою помилку (у промпт не вставлено текст таксономії) і був повторений. "
  "Перевірка: кожне зауваження звірено з визначеннями та is_a-зв'язками SO скриптом; метрики відтворюються запуском python3 sr5.py; SO — публічні дані, персональних даних і ключів API немає.")
p("6. Обмеження",True,sz=12)
p("Один домен і 106 термінів; еталон SO сам має дисбаланс на L1 (61 термін під exon_variant) і неоднозначний вибір «першого батька»; поріг неоднозначності 0,9 довільний; кластеризація залежить від TF-IDF, зв'язування й вибору k=7/18 (узято з ручної); "
  "ручну склала модель, яка знала SO із навчання (до перегляду ієрархії цього піддерева, але не незалежно); лише одна ітерація без людей-експертів; формат — JSON зі зв'язком broader, а не готовий RDF/SKOS. «Ручна» тут означає «побудована зверху вниз за принципом поділу», а не «створена студентом».")
p("7. Самоперевірка",True,sz=12)
p("1. is-a (вид — різновид роду) і part-of (частина — ціле) мають різну транзитивність: змішані, вони дають хибні висновки (напр. «інтрон — це різновид гена»); у нас ділянка (part-of-вісь) і ефект (is-a-вісь) змішані на L1/L2 (дефект 2). "
  "2. Кластеризація знаходить приховані осі й не потребує експерта (NMD-фасет), добре масштабується, але не гарантує біологічного змісту й чутлива до параметрів. 3. Принцип поділу — єдина ознака, за якою діляться сестринські вузли; його змішування породжує перекриття. "
  "4. Стабільні ідентифікатори, зміна лише зв'язків broader, deprecation замість видалення, регресійні тести на метриках.")
d.save('SR5_report.docx')
