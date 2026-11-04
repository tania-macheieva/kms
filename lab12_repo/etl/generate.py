"""Synthetic event generator (documented, deterministic, seed 42).

Business process: variant calling runs in a genomics lab. Source tables written to data/raw/*.csv (what an operational system would export):
  calls_raw.csv         one row per called variant (denormalised, natural keys, strings)  ~20 000 rows (+ a few deliberately dirty rows)
  samples_raw.csv       300 synthetic samples (no personal data: codes S0001..)
  pipelines_raw.csv     pipeline/tool version history (valid_from / valid_to) -> SCD2
  genes_raw.csv         10 hereditary-cancer genes with real chromosomes
  pipeline_day_raw.csv  daily snapshot of the compute queue per pipeline
All distributions are invented for the exercise (see docs/star_design.md, section 'Data generator'); nothing here is real patient data.
"""
import numpy as np, pandas as pd, csv, sys
from pathlib import Path
SEED = 42; N_CALLS = 20000; START, END = "2025-01-01", "2026-09-30"
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

GENES = [("BRCA1", "17", 0.20), ("BRCA2", "13", 0.18), ("TP53", "17", 0.12), ("PALB2", "16", 0.08), ("ATM", "11", 0.10),
         ("CHEK2", "22", 0.08), ("MLH1", "3", 0.06), ("MSH2", "2", 0.06), ("APC", "5", 0.07), ("PTEN", "10", 0.05)]
# family, tool, version, valid_from, valid_to, filter_procedure (taxonomy label in taxonomy_final.csv), qual_shift
PIPES = [("GATK", "HaplotypeCaller", "4.4.0.0", "2025-01-01", "2025-06-30", "hard filtering", -2.0), ("GATK", "HaplotypeCaller", "4.5.0.0", "2025-07-01", "2026-02-28", "hard filtering", 0.0),
         ("GATK", "HaplotypeCaller", "4.6.0.0", "2026-03-01", "9999-12-31", "variant quality score recalibration", 1.0),
         ("BCFTOOLS", "bcftools call", "1.18", "2025-01-01", "2025-09-30", "hard filtering", -4.0), ("BCFTOOLS", "bcftools call", "1.20", "2025-10-01", "9999-12-31", "hard filtering", -3.0),
         ("STRELKA", "Strelka2", "2.9.10", "2025-01-01", "9999-12-31", "hard filtering", 0.5),
         ("DEEPVARIANT", "DeepVariant", "1.6.1", "2025-01-01", "2026-01-14", "hard filtering", 3.0), ("DEEPVARIANT", "DeepVariant", "1.8.0", "2026-01-15", "9999-12-31", "hard filtering", 4.0)]
FAM_W = {"GATK": 0.40, "BCFTOOLS": 0.20, "STRELKA": 0.15, "DEEPVARIANT": 0.25}
TYPES = [("single nucleotide polymorphism", 0.80), ("insertion-deletion", 0.13), ("structural variant", 0.04), ("copy number variation", 0.03)]
SIGN = {"HBOC": [("pathogenic variant", .22), ("variant of uncertain significance", .33), ("benign variant", .45)],
        "Lynch": [("pathogenic variant", .18), ("variant of uncertain significance", .32), ("benign variant", .50)],
        "Control": [("pathogenic variant", .03), ("variant of uncertain significance", .22), ("benign variant", .75)]}

def main(seed=SEED):
    rng = np.random.default_rng(seed); RAW.mkdir(parents=True, exist_ok=True)
    # --- samples
    n_s = 300; cohort = rng.choice(["HBOC", "Lynch", "Control"], n_s, p=[.45, .25, .30]); tissue = rng.choice(["blood", "tumor", "saliva"], n_s, p=[.55, .30, .15])
    samples = pd.DataFrame(dict(sample_code=[f"S{i+1:04d}" for i in range(n_s)], cohort=cohort, tissue=tissue, platform=rng.choice(["NovaSeq", "NextSeq"], n_s, p=[.7, .3]),
                                batch=rng.choice([f"B{i:02d}" for i in range(1, 13)], n_s), qc_status=rng.choice(["pass", "recheck"], n_s, p=[.93, .07])))
    samples.to_csv(RAW / "samples_raw.csv", index=False)
    pd.DataFrame(GENES, columns=["gene_symbol", "chromosome", "weight"]).drop(columns="weight").to_csv(RAW / "genes_raw.csv", index=False)
    pd.DataFrame(PIPES, columns=["family", "tool", "version", "valid_from", "valid_to", "filter_procedure", "qual_shift"]).drop(columns="qual_shift").to_csv(RAW / "pipelines_raw.csv", index=False)
    # --- calls
    dates = pd.date_range(START, END); w = np.linspace(0.8, 1.4, len(dates)); w /= w.sum()          # activity grows over time
    d = rng.choice(dates, N_CALLS, p=w); fam = rng.choice(list(FAM_W), N_CALLS, p=list(FAM_W.values()))
    si = rng.integers(0, n_s, N_CALLS); g = rng.choice(len(GENES), N_CALLS, p=[x[2] for x in GENES])
    vt = rng.choice([t for t, _ in TYPES], N_CALLS, p=[p for _, p in TYPES])
    ver = []
    for fm, dd in zip(fam, d):
        dd = pd.Timestamp(dd).strftime("%Y-%m-%d"); ver.append(next(v for f, t, v, a, b, _, _ in PIPES if f == fm and a <= dd <= b))
    shift = {(f, v): s for f, t, v, a, b, _, s in PIPES}; qs = np.array([shift[(f, v)] for f, v in zip(fam, ver)])
    coh = cohort[si]; tis = tissue[si]
    origin = np.where((tis == "tumor") & (rng.random(N_CALLS) < .7), "somatic variant", "germline variant")
    sig = np.array([SIGN[c][int(rng.choice(3, p=[p for _, p in SIGN[c]]))][0] for c in coh])
    dp = np.clip(rng.lognormal(3.7, .45, N_CALLS) - (vt == "structural variant") * 8, 1, 400).round().astype(int)
    qual = np.clip(rng.gamma(4.0, 9.0, N_CALLS) + qs + (vt == "structural variant") * -5, 1, 200).round(1)
    af = np.where(origin == "somatic variant", rng.beta(2, 8, N_CALLS), np.where(rng.random(N_CALLS) < .35, rng.beta(30, 1, N_CALLS), rng.beta(15, 15, N_CALLS))).round(3)
    pas = ((qual >= 30) & (dp >= 10)); flip = rng.random(N_CALLS) < .03; pas = np.where(flip, ~pas, pas)
    review = np.where(np.isin(sig, ["pathogenic variant", "variant of uncertain significance"]), rng.gamma(2.0, np.where(sig == "pathogenic variant", 6, 3), N_CALLS), 0).round(1)
    calls = pd.DataFrame(dict(call_id=np.arange(1, N_CALLS + 1), call_date=pd.to_datetime(d).strftime("%Y-%m-%d"), sample_code=samples.sample_code.values[si], gene_symbol=[GENES[i][0] for i in g],
                              pipeline_family=fam, pipeline_version=ver, variant_type=vt, origin=origin, clinical_significance=sig, read_depth=dp, qual=qual, alt_fraction=af, is_pass=pas.astype(int), review_minutes=review))
    calls = calls.sort_values(["call_date", "call_id"]).reset_index(drop=True)
    # --- deliberately dirty rows (quarantine demo): negative depth, unknown sample, bad date, null gene, duplicate id
    dirty = calls.sample(5, random_state=1).copy(); dirty["call_id"] = np.arange(N_CALLS + 1, N_CALLS + 6)
    dirty.iloc[0, dirty.columns.get_loc("read_depth")] = -5; dirty.iloc[1, dirty.columns.get_loc("sample_code")] = "S9999"; dirty.iloc[2, dirty.columns.get_loc("call_date")] = "2027-13-45"
    dirty.iloc[3, dirty.columns.get_loc("gene_symbol")] = None; dirty.iloc[4, dirty.columns.get_loc("call_id")] = 17
    pd.concat([calls, dirty]).to_csv(RAW / "calls_raw.csv", index=False)
    # --- daily pipeline snapshot
    rows = []
    for fm in FAM_W:
        q = 20.0   # backlog: mean-reverting random walk
        for dd in dates:
            runs = int(rng.poisson(3 + 2 * (dd.dayofweek < 5))); q = max(0.0, 0.9 * q + rng.normal(0, 3) + runs * 1.2); rows.append((fm, dd.strftime("%Y-%m-%d"), runs, round(runs * rng.uniform(1.5, 4.0), 1), round(q, 1)))
    pd.DataFrame(rows, columns=["pipeline_family", "snap_date", "runs_started", "cpu_hours", "queue_backlog"]).to_csv(RAW / "pipeline_day_raw.csv", index=False)
    print("generated", len(calls) + 5, "call rows,", len(rows), "snapshot rows, seed", seed)

if __name__ == "__main__": main(int(sys.argv[1]) if len(sys.argv) > 1 else SEED)
