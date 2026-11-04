"""Builds dashboard/index.html (self-contained, plotly inlined): 5 questions, 5 charts, each with an interpretation computed from the same data."""
import duckdb, sys, html, json
from pathlib import Path
import plotly.graph_objects as go, plotly.io as pio
from plotly.subplots import make_subplots
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from semantic import sl
con = duckdb.connect(str(ROOT / "data/warehouse.duckdb"), read_only=True)
C = dict(blue="#3b6ea5", orange="#d9822b", green="#5b8c5a", grey="#8a8f98", red="#b5483a")
LAY = dict(template="plotly_white", font=dict(family="Arial", size=12), margin=dict(l=60, r=30, t=50, b=50), height=380)
cards = []
def card(n, question, fig, text, sql_note): cards.append((n, question, pio.to_html(fig, include_plotlyjs=(True if n == 1 else False), full_html=False, config=dict(displaylogo=False)), text, sql_note))

# 1 volume and pass rate per quarter
df = sl.run(con, "call_count", by=["year", "quarter"]).merge(sl.run(con, "pass_rate", by=["year", "quarter"]), on=["year", "quarter"]); df["q"] = df.year.astype(str) + "-Q" + df.quarter.astype(str)
fig = make_subplots(specs=[[{"secondary_y": True}]]); fig.add_bar(x=df.q, y=df.call_count, name="calls", marker_color=C["blue"]); fig.add_scatter(x=df.q, y=df.pass_rate, name="pass rate, %", mode="lines+markers", line=dict(color=C["orange"], width=3), secondary_y=True)
fig.update_yaxes(title_text="calls", secondary_y=False); fig.update_yaxes(title_text="pass rate, %", range=[50, 62], dtick=2, secondary_y=True); fig.update_layout(title="Calls and pass rate per quarter", **LAY)
card(1, "How does call volume and the pass rate develop over time?", fig, f"Volume grew {df.call_count.iloc[-1]/df.call_count.iloc[0]:.1f}× from {df.call_count.iloc[0]:,} calls in {df.q.iloc[0]} to {df.call_count.iloc[-1]:,} in {df.q.iloc[-1]} (the 2026-Q3 bar covers the whole quarter, data end 30 Sep). The pass rate rose from {df.pass_rate.iloc[0]}% to {df.pass_rate.iloc[-1]}% – the quarters after tool upgrades (see chart 3) are the best, so part of the rise is a tool effect, not a data-volume effect.".replace(",", " "), "metrics call_count, pass_rate by year, quarter")

# 2 heatmap family x type
h = con.execute("SELECT p.family, t.label AS vt, round(100.0*sum(f.is_pass)/count(*),1) AS pr, count(*) AS n FROM fact_variant_call f JOIN dim_pipeline p USING(pipeline_key) JOIN dim_taxon t ON t.taxon_key=f.variant_type_key GROUP BY ALL").df()
pv = h.pivot(index="family", columns="vt", values="pr"); order = ["single nucleotide polymorphism", "insertion-deletion", "copy number variation", "structural variant"]; pv = pv[order]
fig = go.Figure(go.Heatmap(z=pv.values, x=["SNP", "indel", "CNV", "SV"], y=pv.index, colorscale="Blues", text=pv.values, texttemplate="%{text}", colorbar=dict(title="pass %"))); fig.update_layout(title="Pass rate (%) by pipeline family and variant type (taxonomy dimension)", **LAY)
sv = h[h.vt == "structural variant"].pr.mean(); snp = h[h.vt == "single nucleotide polymorphism"].pr.mean()
card(2, "Which pipelines and variant types have the lowest pass rate?", fig, f"DeepVariant is best for SNP/indel/CNV (about {pv.loc['DEEPVARIANT'].iloc[0]:.0f}%), bcftools is worst ({pv.loc['BCFTOOLS'].iloc[0]:.1f}% for SNP). Structural variants are the weak spot of every pipeline: {sv:.1f}% on average over the four families against {snp:.1f}% for SNPs. If SVs matter, the plain pass rate underestimates them – they need their own thresholds.", "taxonomy role variant_type × SCD2 family")

# 3 SCD2 effect
m = con.execute("SELECT p.family, d.year, d.month, avg(f.qual) AS q FROM fact_variant_call f JOIN dim_pipeline p USING(pipeline_key) JOIN dim_date d USING(date_key) GROUP BY ALL ORDER BY 1,2,3").df(); m["x"] = m.year.astype(str) + "-" + m.month.astype(str).str.zfill(2)
fig = go.Figure()
for fam, col in (("GATK", C["blue"]), ("BCFTOOLS", C["orange"]), ("DEEPVARIANT", C["green"]), ("STRELKA", C["grey"])): s = m[m.family == fam]; fig.add_scatter(x=s.x, y=s.q.round(1), name=fam, mode="lines", line=dict(color=col, width=2.5 if fam == "GATK" else 1.8))
for x, lab in (("2025-07", "GATK 4.5"), ("2026-03", "GATK 4.6")): fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=1, yref="paper", line=dict(dash="dot", color=C["red"])); fig.add_annotation(x=x, y=1.0, yref="paper", text=lab, showarrow=False, yanchor="bottom", font=dict(color=C["red"], size=11))
fig.update_layout(title="Average call quality per month and family (dotted = GATK version change, SCD2)", yaxis_title="average QUAL", **LAY)
v = con.execute("SELECT p.version, avg(qual) q, 100.0*avg(is_pass) pr FROM fact_variant_call f JOIN dim_pipeline p USING(pipeline_key) WHERE p.family='GATK' GROUP BY 1 ORDER BY 1").df()
card(3, "Did tool upgrades improve the quality of calls?", fig, f"For GATK average quality grew with each release: {v.q[0]:.1f} (4.4.0.0) → {v.q[1]:.1f} (4.5.0.0) → {v.q[2]:.1f} (4.6.0.0), pass rate {v.pr[0]:.1f}% → {v.pr[1]:.1f}% → {v.pr[2]:.1f}%. Other families are flat. Thanks to the SCD2 dimension each call is attributed to the version that really produced it, so the step at the dotted lines is a real before/after comparison (in the synthetic data the generator built this shift in).", "SCD2 dim_pipeline; avg_qual")

# 4 pathogenic per gene
g = con.execute("SELECT g.gene_symbol, g.chromosome, count(*) n FROM fact_variant_call f JOIN dim_sample s USING(sample_key) JOIN dim_gene g USING(gene_key) JOIN dim_taxon t ON t.taxon_key=f.significance_key WHERE s.cohort IN ('HBOC','Lynch') AND s.tissue IN ('blood','tumor') AND t.label='pathogenic variant' GROUP BY ALL ORDER BY n DESC").df()
fig = go.Figure(go.Bar(x=g.gene_symbol, y=g.n, marker_color=[C["red"] if x in ("BRCA1", "BRCA2") else C["blue"] for x in g.gene_symbol], text=g.n, textposition="outside")); fig.update_layout(title="Pathogenic calls per gene (HBOC + Lynch cohorts, blood + tumor samples)", yaxis_title="calls", **LAY)
top2 = g.n.iloc[:2].sum() / g.n.sum() * 100
card(4, "In which genes are the pathogenic calls concentrated (clinically relevant cohorts)?", fig, f"{g.gene_symbol.iloc[0]} ({g.n.iloc[0]}) and {g.gene_symbol.iloc[1]} ({g.n.iloc[1]}) give {top2:.0f}% of {g.n.sum():,} pathogenic calls in the diced sub-cube; PTEN is last ({g.n.iloc[-1]}). The ranking mostly follows how many calls each gene gets in the generator (BRCA1/BRCA2 have the largest weights), so it shows workload, not gene-specific risk.".replace(",", " "), "dice cohort×tissue×significance")

# 5 backlog and cpu
b = sl.run(con, "cpu_hours", by=["year", "month"]).merge(sl.run(con, "avg_daily_backlog", by=["year", "month"]), on=["year", "month"]); b["x"] = b.year.astype(str) + "-" + b.month.astype(str).str.zfill(2)
fig = make_subplots(specs=[[{"secondary_y": True}]]); fig.add_bar(x=b.x, y=b.cpu_hours, name="CPU hours", marker_color=C["blue"]); fig.add_scatter(x=b.x, y=b.avg_daily_backlog, name="avg daily backlog (all families)", mode="lines+markers", line=dict(color=C["orange"], width=3), secondary_y=True)
fig.update_yaxes(title_text="CPU hours", secondary_y=False); fig.update_yaxes(title_text="jobs in queue", secondary_y=True); fig.update_layout(title="Compute: monthly CPU hours (additive) and average daily queue backlog (semi-additive)", **LAY)
mx = b.loc[b.avg_daily_backlog.idxmax()]; mn = b.loc[b.avg_daily_backlog.idxmin()]
card(5, "Is the compute infrastructure becoming a bottleneck?", fig, f"CPU hours stay between {b.cpu_hours.min():,.0f} and {b.cpu_hours.max():,.0f} h per month, and the average daily backlog between {mn.avg_daily_backlog:.0f} ({mn.x}) and {mx.avg_daily_backlog:.0f} ({mx.x}) jobs with no trend – no sign of saturation although call volume grew {df.call_count.iloc[-1]/df.call_count.iloc[0]:.1f}× (chart 1): the queue is simulated independently of the call volume, so this is a limit of the synthetic data. The backlog is aggregated the semi-additive way (sum over families per day, then average over days).".replace(",", " "), "metrics cpu_hours, avg_daily_backlog")

body = "".join(f"<section><h2>{n}. {html.escape(q)}</h2>{ch}<p class='note'><b>Interpretation.</b> {html.escape(t)}</p><p class='src'>Source: {html.escape(s)}</p></section>" for n, q, ch, t, s in cards)
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Variant calling analytics</title>
<style>body{{font-family:Arial,sans-serif;max-width:980px;margin:0 auto;padding:16px;color:#1d2330;background:#fff}}h1{{font-size:22px}}h2{{font-size:17px;margin:28px 0 4px}}section{{border-bottom:1px solid #e3e6ea;padding-bottom:12px}}.note{{background:#f4f7fb;padding:10px 12px;border-left:4px solid #3b6ea5;line-height:1.45}}.src{{color:#6b7280;font-size:12px}}.warn{{background:#fff6e5;border-left:4px solid #d9822b;padding:8px 12px;font-size:13px}}</style></head><body>
<h1>Variant calling analytics – OLAP dashboard</h1><p class="warn">Synthetic data (etl/generate.py, seed 42, dataset v1.0.0, 20 000 calls). The interpretations describe what the generator built in; they are not medical findings.</p>{body}</body></html>"""
(ROOT / "dashboard/index.html").write_text(page, encoding="utf-8"); print("dashboard ok", len(cards), "charts", round(len(page) / 1e6, 1), "MB")
