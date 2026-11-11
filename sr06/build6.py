import sys, json, collections
sys.path.insert(0,'.'); import sr6
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
K=['K1','K2','K3','K4','K5']; maps=['expert','llm','peer']
NAME={'expert':'Власна (ЛР6, v1)','llm':'LLM-карта','peer':'«Колега» (LLM)'}
S=json.load(open('scores_all.json')); AG=json.load(open('agreement_all.json')); AG12=json.load(open('agreement.json'))
R1b=json.load(open('R1b_scores.json')); R3=json.load(open('R3_informed.json'))
MET=json.load(open('metrics.json'))
tot=lambda v:sum(v)
# ---------- ДІАГРАМА
fig,ax=plt.subplots(1,2,figsize=(10,3.8),gridspec_kw={'width_ratios':[1.5,1]})
w=0.26; x=range(3); cols={'R1':'#2b6cb0','R2':'#dd8a1e','R3':'#8a8a8a'}
for j,r in enumerate(['R1','R2','R3']):
    vals=[tot(S[r][m]) for m in maps]
    b=ax[0].bar([i+(j-1)*w for i in x],vals,w,color=cols[r],hatch='//' if r=='R3' else None,edgecolor='white',label={'R1':'R1 Sonnet (наосліп)','R2':'R2 Haiku (наосліп)','R3':'R3 обізнана (не незалежна)'}[r])
    for i,v in enumerate(vals): ax[0].text(i+(j-1)*w,v+0.15,str(v),ha='center',fontsize=9)
ax[0].set_xticks(list(x)); ax[0].set_xticklabels([NAME[m] for m in maps],fontsize=9); ax[0].set_ylim(0,11.5); ax[0].set_ylabel('Сума за рубрикою, 0–10')
ax[0].legend(fontsize=8,frameon=False,loc='upper left'); ax[0].set_title('Оцінки трьох карт',fontsize=11)
lab=['Оригінал\n(R1, запуск 1)','Оригінал\n(R1b, запуск 2)','Виправлена\n(R1b)']
v=[tot(S['R1']['llm']),tot([R1b['llm_original'][k] for k in K]),tot([R1b['fixed'][k] for k in K])]
bars=ax[1].bar(range(3),v,0.55,color=['#b9b9b9','#b9b9b9','#1a8a3a'])
for i,t in enumerate(v): ax[1].text(i,t+0.15,str(t),ha='center',fontsize=9)
ax[1].set_xticks(range(3)); ax[1].set_xticklabels(lab,fontsize=8); ax[1].set_ylim(0,11.5); ax[1].set_title('LLM-карта до і після виправлень',fontsize=11)
for a in ax:
    a.spines[['top','right']].set_visible(False)
plt.tight_layout(); plt.savefig('chart_scores.png',dpi=170); plt.close()
# ---------- ВИПРАВЛЕННЯ
FIXTXT=[
("F01","E1","L032–L034, L038–L039: detects BRCA1/BRCA2/genetic variant → cascade testing detects pathogenic variant; genetic testing detects pathogenic variant (крос-зв'язок)","Шукають варіант у гені, а не сам ген; джерело: «checked for the same genetic change that you have»"),
("F02","E2","L011 rank sum test applies_to allele — видалено","Тест порівнює якості мапування ридів, allele — лише умова; зміст уже є в L010 (rank sum test uses_input mapping quality)"),
("F03","E2","L041 genetic counseling produces risk assessment → risk assessment applies_to relative","Порушував range відношення produces; у джерелі консультант допомагає з оцінками ризику для родичів"),
("F04","E3","L030 genetic variant increases_risk_of hereditary cancer → pathogenic variant increases_risk_of hereditary cancer (крос-зв'язок); додано pathogenic variant is_a genetic variant, BRCA1/BRCA2 is_a gene","Ризик підвищує лише патогенний варіант; додано рівень ієрархії"),
("F05","E4","L015 VQSR requires genetic variant → requires large set of variants; requires known variant resources","Тривіальне ребро замінено умовами з джерела (gatk)"),
("F06","E5","L036/L037 recommended_for breast/ovarian cancer + уточнення «для деяких пацієнтів»","У джерелі тестування рекомендоване лише для деяких; більшість раків не спадкові"),
("F07","E0","Порогові значення з контекстом: FS > 60 (SNP); додано FS > 200 (INDEL), MQRankSum < −12,5, ReadPosRankSum < −8","Для INDEL поріг інший (gatk, коментар); значення подано екземплярами"),
("F08","E7","L020: слабку цитату (заголовок) замінено на «substitute for VQSR (the method we normally recommend for filtering germline short variants)»","Підстава пропозиції має підтримувати твердження"),
("F09","E6","Додано ієрархію родичів (first/second/third-degree is_a relative) з 50 %/25 %/до 12,5 %, cascade testing recommended_for first-degree relative (крос-зв'язок), age ≥ 18","Відсутня друга половина фокусного питання; усе — з cdc"),
("F10","E6","Додано крос-зв'язки: hard filtering recommended_for gene panel; cascade testing requires pathogenic variant","Дві гілки карти були майже не зв'язані; обидва зв'язки підтверджені цитатами"),
]
# ---------- XLSX
wb=Workbook(); H=lambda ws:[setattr(c,'font',Font(bold=True)) or setattr(c,'fill',PatternFill('solid',fgColor='D9E2F3')) or setattr(c,'alignment',Alignment(wrap_text=True,vertical='top')) for c in ws[1]]
def wrapcols(ws,widths):
    for i,wd in enumerate(widths): ws.column_dimensions[chr(65+i)].width=wd
    for row in ws.iter_rows(min_row=2):
        for c in row: c.alignment=Alignment(wrap_text=True,vertical='top')
ws=wb.active; ws.title='Рубрика'
ws.append(['Критерій','0','1','2'])
for r in [("K1 Пропозиції (кількість і точність)","<10 або більшість неточні","≥15, але помітна частка неточних/тривіальних/дубльованих","≥30, майже всі точні, без дублів"),
("K2 Ієрархія","плоска","2 рівні або непослідовна","≥3 чіткі послідовні рівні"),
("K3 Крос-зв'язки","немає","1–2, слабкі або без пояснень","≥3 змістовні, пояснені, нетривіальні"),
("K4 Приклади","немає","1–4 або нерелевантні","≥5 конкретних релевантних"),
("K5 Фокусне питання і 18 CQ","практично ні на що","на частину (напр. одну з двох частин питання)","на обидві частини питання і більшість CQ")]: ws.append(list(r))
H(ws); wrapcols(ws,[34,26,46,44])
ws=wb.create_sheet('Оцінки'); ws.append(['Карта','Оцінювач','K1','K2','K3','K4','K5','Сума /10','Незалежний?'])
for m in maps:
    for r,ind in (('R1','так, наосліп'),('R2','так, наосліп'),('R3','ні (після R1/R2)')):
        n=ws.max_row+1; ws.append([NAME[m],r]+S[r][m]+[f'=SUM(C{n}:G{n})',ind])
    n=ws.max_row+1; ws.append([NAME[m],'Студент (заповнити)',None,None,None,None,None,f'=SUM(C{n}:G{n})','—'])
for nm,key in (('LLM-карта оригінал (R1b)','llm_original'),('LLM-карта виправлена (R1b)','fixed')):
    n=ws.max_row+1; ws.append([nm,'R1b (наосліп, пара карт)']+[R1b[key][k] for k in K]+[f'=SUM(C{n}:G{n})','так'])
H(ws); wrapcols(ws,[34,26,6,6,6,6,6,10,22])
ws=wb.create_sheet('Узгодженість'); ws.append(['Пара','Сер. |різниця|','Точний збіг','В межах 1','Спірмен','Квадр. κ','Примітка'])
nt={'R1-R2':'основна: обидва наосліп, різні моделі','R1-R3':'R3 бачила R1/R2','R2-R3':'завищено: R3 складено після R1/R2'}
for k,v in AG.items():
    if '-' in k and k!='totals': ws.append([k,v['mean_abs_diff'],v['exact'],v['within1'],v['spearman'],v['kappa_quadratic'],nt[k]])
ws.append([]); ws.append(['R1–R2 за критеріями (сер. |різниця|)']+[f"{k}={v}" for k,v in AG12['by_crit'].items()])
ws.append(['R1–R2 за картами']+[f"{NAME[k]}={v}" for k,v in AG12['by_map'].items()])
ws.append(['Найбільші розбіжності R1 vs R2 (різниця 1)']+[f"{NAME[m]} {k}: {a} vs {b}" for m,k,a,b in AG12['biggest']])
ws.append(['Різниця сум R1−R2']+[f"{NAME[m]}: {d}" for m,d in AG12['total_diff'].items()])
H(ws); wrapcols(ws,[40,16,14,12,10,10,44])
ws=wb.create_sheet('Метрики карт'); ws.append(['Метрика','Власна','LLM','Колега','LLM виправлена'])
MM=[('Понять','concepts'),('Екземплярів','instances'),('Пропозицій','propositions'),('«related to», %','related_to_pct'),('Типів відношень','relation_types'),('Рівнів ієрархії','max_hierarchy_levels'),('Крос-зв\'язків із поясненням','bridging_explained'),('Компонент зв\'язності','components')]
for lab,k in MM: ws.append([lab]+[MET[m][k] for m in ('expert','llm','peer','llm_fixed')])
A=MET['audit']
ws.append(['Пропозицій із вадами за аудитом (%)',f"{A['expert']['n']}/{A['expert']['total']} ({100*A['expert']['n']/A['expert']['total']:.0f} %)",f"{A['llm']['n']}/{A['llm']['total']} ({100*A['llm']['n']/A['llm']['total']:.0f} %)",f"{A['peer']['n']}/{A['peer']['total']} ({100*A['peer']['n']/A['peer']['total']:.0f} %)",'—'])
H(ws); wrapcols(ws,[40,18,18,18,20])
ws=wb.create_sheet('Аудит пропозицій'); ws.append(['Карта','ID','Пропозиція','Клас','Серйозність 1–3','Примітка'])
for mp,aud,M in (('LLM',sr6.AUD_LLM,sr6.MAPS['llm']),('Колега',sr6.AUD_PEER,sr6.MAPS['peer']),('Власна',sr6.AUD_EXP,sr6.MAPS['expert'])):
    by={e['id']:e for e in M['edges']}
    for i,(c,s,n) in aud.items(): e=by[i]; ws.append([mp,i,f"{e['s']} —{e['p']}→ {e['o']}",c,s,n])
H(ws); wrapcols(ws,[10,8,60,8,12,80])
ws=wb.create_sheet('Виправлення'); ws.append(['№','Клас помилки','Що змінено','Чому / джерело'])
for r in FIXTXT: ws.append(list(r))
H(ws); wrapcols(ws,[6,12,90,70])
ws=wb.create_sheet('Нові пропозиції'); ws.append(['ID','Пропозиція','Крос-зв\'язок','Статус','Джерело (цитата перевірена в тексті)','Виправлення'])
for e in sr6.FIXED['edges']:
    if e['id'].startswith('N'): ws.append([e['id'],f"{e['s']} —{e['p']}→ {e['o']}",'так' if e['cross'] else '',e['status'],e.get('source',''),e['fix']])
H(ws); wrapcols(ws,[7,70,12,16,70,12])
CATD=[("E0","Порогове значення як літерал / без контексту","QD < 2; FS > 60 без «для SNP»","використовувати екземплярні вузли з типом варіанта; перевіряти умови застосовності"),
("E1","Змішування сутностей (ген замість варіанта; хвороба замість пацієнтів)","cascade testing detects BRCA1","у підказці вказувати типи domain/range; автоперевірка типів"),
("E2","Хибне відношення або порушення domain/range","genetic counseling produces risk assessment; rank sum test applies_to allele","закритий каталог відношень + перевірка типів; ручний перегляд семантики"),
("E3","Надмірне узагальнення, категорна помилка","genetic variant increases_risk_of hereditary cancer; breast cancer is_a hereditary cancer","вимагати найвужчого суб'єкта; перевіряти кожне is_a правилом «чи завжди так?»"),
("E4","Тривіальне або надлишкове ребро","VQSR requires genetic variant","фільтр «інформативності»: ребро має відповідати на CQ"),
("E5","Втрата квантора/умови/повноти","recommended_for breast cancer (у джерелі «для деяких»)","вимагати дослівну цитату й перевіряти квантори"),
("E6","Відсутні крос-зв'язки, ізольовані гілки","LLM-карта: 0 пояснених крос-зв'язків з 41","окремий крок: «запропонуй зв'язки між кластерами з поясненням і цитатою»"),
("E7","Слабка підстава","evidence — заголовок статті","автоперевірка цитати + ручна перевірка, що вона підтримує твердження"),
("E8","Сумнівний напрямок / мета як адресат","variant filtering recommended_for data quality","перевіряти читання пропозиції як речення"),
("E9","Твердження поза джерелами","cascade testing requires informed consent","позначати статус verified / expert_asserted, не змішувати")]
ws=wb.create_sheet('Каталог помилок'); ws.append(['Клас','Опис','Приклад','Контрзахід','LLM-карта','Колега','Власна'])
for c,d,ex,cm in CATD:
    ws.append([c,d,ex,cm]+[A[m]['by_class'].get(c,0) for m in ('llm','peer','expert')])
ws.cell(row=2+6,column=5).value=1  # E6: на рівні карти (немає пояснених крос-зв'язків)
H(ws); wrapcols(ws,[7,48,56,60,12,10,10])
wb.save('SR6_concept_maps_assessment.xlsx')
print('xlsx ok')
json.dump(dict(CATD=CATD,FIXTXT=FIXTXT),open('tables.json','w'),ensure_ascii=False)
