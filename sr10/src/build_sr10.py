import json, numpy as np
from pathlib import Path
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Pt, Cm
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
R=Path(__file__).resolve().parents[1]
res=json.load(open(R/'eval/results.json')); P=json.load(open(R/'eval/perq.json')); M=res['models']
G=[g for g in map(json.loads,open(R/'eval/gold_lab10.jsonl')) if g['answerable']]
NAMES={'minilm':'MiniLM-L6 (EN)','bge':'BGE-small (EN)','e5':'mE5-small (multi)','potion':'potion-8M (EN, статична)','bm25':'BM25 (лексична)'}
ORDER=['minilm','bge','e5','potion','bm25']
# --- парні bootstrap-різниці R@5 (проти bge)
def pdiff(a,b,B=4000):
    x=np.array([p['r5'] for p in P[a]])-np.array([p['r5'] for p in P[b]]); rng=np.random.default_rng(1)
    bs=[x[rng.integers(0,len(x),len(x))].mean() for _ in range(B)]; return round(float(x.mean()),3),[round(float(np.percentile(bs,2.5)),3),round(float(np.percentile(bs,97.5)),3)]
PD={m:pdiff(m,'bge') for m in ORDER if m!='bge'}
# --- чутливість: без 4 перефразувань із легким зсувом змісту (позначено вручну)
FLAG={'Q10','Q20','Q24','Q31'}; keep=[i for i,g in enumerate(G) if g['qid'] not in FLAG]
sens={m:(round(float(np.mean([P[m][i]['r5'] for i in keep])),3),round(float(np.mean([P[m+'_para'][i]['r5'] for i in keep])),3)) for m in ORDER}
# --- графік
fig,ax=plt.subplots(1,2,figsize=(10,3.1)); cols=['#4c78a8','#f58518','#54a24b','#b279a2','#7f7f7f']
x=np.arange(len(ORDER)); w=0.27
for k,(lab,key) in enumerate([('EN (47)','en'),('UK (8)','uk')]):
    ax[0].bar(x+(k-0.5)*w*1.2,[M[m]['by'][key]['r5'] for m in ORDER],w*1.2,label=lab,color=['#4c78a8','#e45756'][k])
ax[0].set_xticks(x); ax[0].set_xticklabels([n.split(' (')[0] for n in [NAMES[m] for m in ORDER]],fontsize=7); ax[0].set_ylabel('recall@5',fontsize=8); ax[0].set_ylim(0,1); ax[0].legend(fontsize=7); ax[0].set_title('Мова запиту',fontsize=9)
for i,m in enumerate(ORDER): ax[1].scatter(M[m]['lat_ms_median'],M[m]['overall']['r5'],s=60,color=cols[i]); ax[1].annotate(NAMES[m].split(' (')[0],(M[m]['lat_ms_median'],M[m]['overall']['r5']),fontsize=7,xytext=(4,3),textcoords='offset points')
ax[1].set_xscale('log'); ax[1].set_xlabel('медіанна затримка запиту, мс (лог.)',fontsize=8); ax[1].set_ylabel('recall@5',fontsize=8); ax[1].set_title('Якість проти затримки (n=55)',fontsize=9); ax[1].set_ylim(0.3,0.9)
for a in ax: a.tick_params(labelsize=7); a.spines[['top','right']].set_visible(False)
plt.tight_layout(); plt.savefig(R/'eval/fig_sr10.png',dpi=200); plt.close()
# --- таблиці
T1=[(NAMES[m],M[m]['dim'] or '—',M[m]['model_mb'],M[m]['index_mb'] or '—',M[m]['index_build_s'] if M[m]['index_build_s'] is not None else '—',f"{M[m]['lat_ms_median']} / {M[m]['lat_ms_p95']}",f"{M[m]['overall']['r5']:.3f} [{M[m]['ci_r5'][0]}–{M[m]['ci_r5'][1]}]",f"{M[m]['overall']['mrr']:.3f}",f"{M[m]['overall']['ndcg']:.3f}") for m in ORDER]
T2=[(NAMES[m],*[f"{M[m]['by'][k]['r5']:.2f}" for k in ('en','uk_cross','uk_internal','keyword','paraphrase','multi_step')],f"{M[m]['para_overall']['r5']:.3f}",f"{M[m]['para_overall']['r5']-M[m]['overall']['r5']:+.3f}") for m in ORDER]
DIV=[('Q03 (перефраз.)','minilm ✔(1), bge ✔(3), e5 ✘(15), BM25 ✘(12)','Заголовок золотого чанка («Which variant calling tool is implemented for which data type?») майже збігається зі змістом запиту — це ловлять щільні моделі; BM25 не має спільних слів із «GPU-accelerated germline caller» і підняв Parabricks DeepSomatic (соматичний). e5 віддав перевагу чанку про sample sheet.'),
('Q06 (перефраз.)','minilm ✔(1), BM25 ✔(1), bge ✘(33), e5 ✘(6)','Золотий чанк — «Sentieon BWA mem» (комерційний вирівнювач); запит каже «proprietary mapper». minilm/BM25 схопили «alignment files»/«saved»; bge підняв Sentieon Dedup (той самий вендор, інший крок), e5 — сторонній bcftools. Причину для bge/e5 не перевіряв (гіпотеза: вендор переважив дію).'),
('Q09 (ключ.)','minilm ✔(2), e5 ✔(2), BM25 ✔(1), bge ✘(14)','Золотий чанк — розділ «2.0 – Requirements». BM25 вхопив слово requirements. bge, ймовірно, поставив вище загальний розділ «Funcotator Background» (інструкція-префікс bge розрахована на питання, а запит — набір слів; це гіпотеза).'),
('Q13 (перефраз.)','усі щільні ✘ (10–64), BM25 ✔(1)','Золоте речення майже дослівно «right-align variants in transcripts». Рідкісні терміни працюють на користь лексичного пошуку; щільні моделі пішли за темою «annotation / variant» до чанка про Funcotator.'),
('Q29 (укр.→англ.)','bge ✔(1), e5 ✔(3), minilm ✘(47), BM25 ✘(37)','Мова: українське питання з латинським «DeepVariant» до англійського документа. bge і e5 знайшли; minilm підняв українські чанки внутрішніх документів. Для e5 топ-1 — теж український чанк (ознака «зсуву до мови запиту»). Вибірка 4 запити — висновок про мову лише орієнтовний.'),
('Q44 (укр.→укр.)','bge ✔(1), e5 ✔(1), BM25 ✔(5), minilm ✘(6)','Золотий чанк: «Сховище: pyoxigraph…». minilm підняв сусідній чанк того самого документа (federated query) — близька, але не та частина. Помилка «правильний документ, сусідній чанк».'),
('Q35 (перефраз.)','bge ✔(3), BM25 ✔(1), minilm ✘(21), e5 ✘(>100)','Золоте речення містить «small tutorial dataset» і «filtering». e5 не вивів його навіть у топ-100: схоже, вузький діапазон косинусів int8-моделі гірше розрізняє чанки; це гіпотеза.')]
# --- xlsx
wb=Workbook(); wb.remove(wb.active); HF=Font(bold=True,color='FFFFFF'); FL=PatternFill('solid',fgColor='305496'); W=Alignment(wrap_text=True,vertical='top')
def sh(n,h,r,w):
    ws=wb.create_sheet(n); ws.append(h)
    for c in ws[1]: c.font=HF; c.fill=FL; c.alignment=W
    for x in r: ws.append(list(x))
    for i,v in enumerate(w): ws.column_dimensions[chr(65+i)].width=v
    for row in ws.iter_rows(min_row=2):
        for c in row: c.alignment=W
sh('Підсумок',['Модель','dim','Модель, МБ','Індекс, МБ','Побудова, с','Затримка мед./p95, мс','recall@5 [95% CI]','MRR@10','nDCG@10'],T1,[26,6,12,12,12,20,24,10,10])
sh('За підмножинами',['Модель','EN r@5','UK→EN r@5','UK→UK r@5','keyword','paraphrase','multi_step','recall@5 на перефраз. запитах','Δ'],T2,[26,10,12,12,10,12,12,26,8])
rows=[]
for i,g in enumerate(G):
    rows.append((g['qid'],g['type'],g['query'],*[f"{P[m][i]['r5']:.2f} / ранг {P[m][i]['first_rank']}" for m in ORDER]))
sh('По запитах',['QID','Тип','Запит']+[NAMES[m] for m in ORDER],rows,[6,12,70,18,18,18,18,18])
sh('Розбіжності',['Запит','Результат (ранг першого золотого)','Пояснення'],DIV,[18,42,110])
sh('Парні різниці',['Модель','Δ recall@5 проти BGE','95% CI'],[(NAMES[m],PD[m][0],str(PD[m][1])) for m in PD],[26,22,24])
sh('Нормалізація',['Модель','recall@5 косинус','recall@5 dot без нормалізації','Сер. норма вектора пасажа'],[(NAMES[m],M[m]['overall']['r5'],M[m]['unnormalized_dot']['r5'],M[m]['mean_norm_passages_unnorm']) for m in ('minilm','e5')],[26,18,26,24])
sh('Чутливість',['Модель','recall@5 без 4 позначених перефраз.','recall@5 перефраз. без 4 позначених'],[(NAMES[m],*sens[m]) for m in ORDER],[26,32,32])
wb.save(R/'SR10_embeddings_results.xlsx')
# --- docx
d=Document(); s=d.sections[0]; s.page_width=Cm(21); s.page_height=Cm(29.7)
for a in ('left_margin','right_margin'): setattr(s,a,Cm(1.4))
s.top_margin=Cm(1.1); s.bottom_margin=Cm(1.0)
st=d.styles['Normal']; st.font.name='Calibri'; st.font.size=Pt(8.5); st.element.rPr.rFonts.set(qn('w:eastAsia'),'Calibri'); st.paragraph_format.space_after=Pt(1.5)
def Pp(t,b=False,sz=None):
    p=d.add_paragraph(); r=p.add_run(t); r.bold=b
    if sz: r.font.size=Pt(sz)
def shade(c):
    t=c._tc.get_or_add_tcPr(); e=OxmlElement('w:shd'); e.set(qn('w:val'),'clear'); e.set(qn('w:fill'),'D9E2F3'); t.append(e)
def tab(h,r,w,fs=7.5):
    t=d.add_table(rows=1,cols=len(h)); t.style='Table Grid'; t.autofit=False
    for i,x in enumerate(h):
        c=t.rows[0].cells[i]; c.text=''; rr=c.paragraphs[0].add_run(x); rr.bold=True; rr.font.size=Pt(fs); shade(c)
    for row in r:
        cs=t.add_row().cells
        for i,v in enumerate(row): cs[i].text=''; cs[i].paragraphs[0].add_run(str(v)).font.size=Pt(fs)
    for i,x in enumerate(w): t.columns[i].width=Cm(x)
    for row in t.rows:
        for i,x in enumerate(w): row.cells[i].width=Cm(x)
        for c in row.cells:
            for p in c.paragraphs: p.paragraph_format.space_after=Pt(0)
Pp('Самостійна робота 10. Експеримент з embeddings',True,12.5)
Pp(f"Корпус: {res['n_chunks']} фрагментів документації (GATK, nf-core/sarek, raredisease, bcftools + внутрішні українські документи, з ЛР10); {res['n_queries']} запитів із золотою розміткою за спанами (47 англ., 8 укр.: 4 укр.→англ. і 4 укр.→укр.; 10 запитів із 2 доказами). Метрики: recall@5, MRR@10, nDCG@10 (збіг чанка зі спаном ≥50%). Моделі: all-MiniLM-L6-v2 (int8), bge-small-en-v1.5, multilingual-e5-small (int8) — єдина мультимовна, potion-base-8M (статична) та BM25 як ненейронний базовий рівень. Ваги — публічні ONNX-експорти з npm-пакетів (HuggingFace недоступний), CPU 2 vCPU, без GPU.")
Pp('1. Результати',True,10)
tab(['Модель','dim','Модель МБ','Індекс МБ','Побудова, с','Затримка мед./p95, мс','recall@5 [95% CI]','MRR@10','nDCG@10'],T1,[3.5,0.9,1.4,1.4,1.5,2.4,3.4,1.5,1.5])
Pp('Затримка = кодування одного запиту + пошук (повний перебір) на 688 фрагментах, медіана 55 запитів після прогріву. Індекс — fp32, 688×dim.')
d.add_picture(str(R/'eval/fig_sr10.png'),width=Cm(16.5))
tab(['Модель','EN (47)','UK→EN (4)','UK→UK (4)','keyword (17)','paraphrase (20)','multi_step (10)','r@5 на LLM-перефраз.','Δ'],T2,[3.5,1.4,1.6,1.6,1.8,1.9,1.9,2.6,1.2])
Pp(f"Статистика: 95% довірчі інтервали перекриваються; парна різниця recall@5 проти BGE — MiniLM {PD['minilm'][0]:+.3f} {PD['minilm'][1]}, mE5 {PD['e5'][0]:+.3f} {PD['e5'][1]}, BM25 {PD['bm25'][0]:+.3f} {PD['bm25'][1]}, potion {PD['potion'][0]:+.3f} {PD['potion'][1]} — тож BGE, MiniLM, mE5 та BM25 статистично не розрізняються на 55 запитах; лише potion помітно слабший. Перефразування (LLM Claude Haiku, перевірено мною: у 4 з 55 зсув змісту — Q10, Q20, Q24, Q31; без них висновки ті самі) найбільше зменшили BM25 (−0.136) і MiniLM (−0.073); BGE не зменшилась (+0.027).")
Pp('2. П’ять і більше розбіжностей (з 32 із 55 запитів, де моделі розходяться)',True,10)
tab(['Запит','Результат (ранг першого золотого)','Пояснення (гіпотези позначено)'],DIV,[2.4,4.6,11.7],7)
Pp('3. Висновок: мова, домен, вартість',True,10)
Pp(f"Якість на цій колекції майже однакова (recall@5 0.73–0.76) у BGE, BM25, MiniLM, mE5; BGE має кращі MRR/nDCG та стійкість до перефразування, але затримка в {M['bge']['lat_ms_median']/M['minilm']['lat_ms_median']:.0f}× вища за MiniLM, побудова індексу {M['bge']['index_build_s']/M['minilm']['index_build_s']:.0f}× довша, модель 133 МБ. Мова: мультимовна mE5 не дала переваги над англійськими моделями на українських запитах (UK→EN 0.25 проти 0.25 у BGE; UK→UK 1.00 проти 1.00) — вибірка 8 запитів надто мала для висновку; MiniLM помітно слабший на UK→EN (0.00). Домен: ключові та рідкісні термінологічні запити (keyword r@5 = 1.00 у BM25 і MiniLM; Q13 лише BM25) — сильний бік лексичного пошуку; на перефразуваннях він найслабший. Вартість: potion — найшвидший (0.15 мс) і найменший індекс, але якість лише 0.46; усі інші працюють на CPU без API-витрат. Практично для такого корпусу розумно розглянути гібрид BM25 + щільна модель (BGE або mE5 за потреби української) — це гіпотеза, у цій роботі НЕ перевірена.")
Pp('4. Самоперевірка',True,10)
Pp(f"1) Нормалізація: після L2-нормалізації скалярний добуток = косинус, довжина тексту не впливає. Експеримент: MiniLM recall@5 {M['minilm']['overall']['r5']:.3f} (cos) → {M['minilm']['unnormalized_dot']['r5']:.3f} (dot без нормалізації); mE5 {M['e5']['overall']['r5']:.3f} → {M['e5']['unnormalized_dot']['r5']:.3f}. 2) Дотреновувати — коли є розмічені пари домену, а помилки системні (спеціальна термінологія, мова), і базові моделі та гібрид вже вичерпано; тут не робилось. 3) Мова: англійські моделі, ймовірно, спираються на латинські терміни (DeepVariant, SPARQL) в українських запитах, але нестабільно (Q29/Q44 для MiniLM); у Q29 топ-1 mE5 — український чанк, тобто можливий зсув до мови запиту (один приклад). 4) Обмеження — нижче.")
Pp('5. Обмеження та декларація використання ШІ',True,10)
Pp("Обмеження: 55 запитів, з них 8 українських (по 4) — підмножини статистично слабкі; золота розмітка з ЛР10 (одна розмітка, без другого оцінювача); заголовки чанків містять шум (напр. «Required and defaults to false. — …») і входять до тексту для embeddings; квантовані int8 експорти (MiniLM, mE5) відрізняються від fp32 оригіналів; potion — власна реалізація інференсу; затримка виміряна на 2 vCPU, у процесі, без мережі; пояснення розбіжностей — з читання топ-1 чанків, причини для щільних моделей не доведені абляціями; гібрид і дотренування не перевірялись. Декларація ШІ: модель Claude (Anthropic) — код експерименту, звіт; «сліпий» LLM (Claude Haiku) — перефразування запитів. Приклад запиту: «Для кожного пошукового запиту дай ОДНЕ перефразування тією ж мовою, зберігши намір». Перевірка: читання всіх 55 перефразувань (4 з легким зсувом змісту позначено), метрики — виконанням коду. Студент має перевірити пояснення розбіжностей на своїх даних.")
d.save(R/'SR10_report.docx'); print('built', PD, sens)
