#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

RESULT_PATTERN = re.compile(r'(?P<topology>[^_]+)_(?P<algorithm>.+)_rate(?P<rate>\d+)_seed(?P<seed>\d+)\.csv$')

ALGO_ORDER = ["distance", "keyaware", "random", "ga_tcheby_proxy"]
TOPO_ORDER = ["mesh9", "mesh16", "irregular12", "ring6"]
TOPO_SIZE = {"ring6": 6, "mesh9": 9, "irregular12": 12, "mesh16": 16}

def parse_meta(path: Path):
    m = RESULT_PATTERN.match(path.name)
    if not m:
        return None
    d = m.groupdict()
    d["rate"] = int(d["rate"])
    d["seed"] = int(d["seed"])
    return d

def ci95(x):
    x = pd.Series(x).dropna().astype(float)
    if len(x) <= 1:
        return 0.0
    return float(1.96 * x.std(ddof=1) / np.sqrt(len(x)))

def load_runs(results_dir: Path) -> pd.DataFrame:
    frames = []
    for p in sorted(results_dir.glob("*.csv")):
        meta = parse_meta(p)
        if not meta:
            continue
        df = pd.read_csv(p)
        if df.empty:
            continue
        for k, v in meta.items():
            df[k] = v
        frames.append(df)
    if not frames:
        raise SystemExit(f"No run CSVs found in {results_dir}")
    return pd.concat(frames, ignore_index=True)

def select_representative_rate(summary: pd.DataFrame, topo: str):
    ss = summary[summary["topology"] == topo].groupby("rate", as_index=False)["blocking_probability"].mean()
    if ss.empty:
        return None
    ss["score"] = (ss["blocking_probability"] - 0.5).abs()
    return int(ss.sort_values(["score", "rate"]).iloc[0]["rate"])

def parse_path(s):
    if pd.isna(s):
        return []
    s = str(s).strip()
    if s == "[]" or s == "":
        return []
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    if not s:
        return []
    try:
        return [int(tok) for tok in s.split("-")]
    except Exception:
        return []

def build_link_count_matrix(df: pd.DataFrame, topo: str, alg: str, rate: int):
    ss = df[(df["topology"] == topo) & (df["algorithm"] == alg) & (df["rate"] == rate) & (df["blocked"] == 0)]
    n = TOPO_SIZE.get(topo, None)
    if n is None:
        n = int(max(ss["src"].max(), ss["dst"].max()) + 1)
    mat = np.zeros((n, n), dtype=float)
    for _, row in ss.iterrows():
        path = parse_path(row["path"])
        for u, v in zip(path[:-1], path[1:]):
            if 0 <= u < n and 0 <= v < n:
                mat[u, v] += 1
    return mat

def main():
    import sys
    if len(sys.argv) < 3:
        raise SystemExit("Usage: make_qflow_omnet_final_figures.py <results_dir> <out_dir>")
    results_dir = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    raw = load_runs(results_dir)

    run_level = raw.groupby(["topology","algorithm","rate","seed"], as_index=False).agg(
        blocking_probability=("blocked","mean"),
        mean_bottleneck_fidelity=("bottleneck_fidelity", lambda s: float(pd.Series(s)[pd.Series(s) > 0].mean()) if (pd.Series(s) > 0).any() else 0.0),
        mean_max_utilization=("max_utilization","mean"),
        mean_hops=("hops","mean"),
        mean_distance_km=("distance_km","mean"),
        mean_decision_latency_ms=("decision_latency_ms","mean"),
        requests=("request_id","count"),
        served=("blocked", lambda s: int((1-pd.Series(s)).sum())),
        blocked=("blocked", "sum"),
    )

    summary = run_level.groupby(["topology","algorithm","rate"], as_index=False).agg(
        blocking_probability=("blocking_probability","mean"),
        blocking_ci95=("blocking_probability", ci95),
        mean_bottleneck_fidelity=("mean_bottleneck_fidelity","mean"),
        fidelity_ci95=("mean_bottleneck_fidelity", ci95),
        mean_max_utilization=("mean_max_utilization","mean"),
        util_ci95=("mean_max_utilization", ci95),
        mean_hops=("mean_hops","mean"),
        mean_distance_km=("mean_distance_km","mean"),
        mean_decision_latency_ms=("mean_decision_latency_ms","mean"),
        latency_ci95=("mean_decision_latency_ms", ci95),
        total_runs=("seed","count"),
    )

    summary["algorithm"] = pd.Categorical(summary["algorithm"], categories=ALGO_ORDER, ordered=True)
    summary["topology"] = pd.Categorical(summary["topology"], categories=TOPO_ORDER, ordered=True)
    summary = summary.sort_values(["topology","rate","algorithm"]).reset_index(drop=True)

    run_level.to_csv(out_dir / "omnet_final_run_level_summary.csv", index=False)
    summary.to_csv(out_dir / "omnet_final_summary.csv", index=False)

    representative_rows = []
    for topo in [t for t in TOPO_ORDER if t in set(summary["topology"].astype(str))]:
        rep_rate = select_representative_rate(summary, topo)
        if rep_rate is None:
            continue
        representative_rows.append({"topology": topo, "representative_rate": rep_rate})
    rep_df = pd.DataFrame(representative_rows)
    rep_df.to_csv(out_dir / "omnet_representative_rates.csv", index=False)

    for topo in [t for t in TOPO_ORDER if t in set(summary["topology"].astype(str))]:
        ss = summary[summary["topology"].astype(str) == topo]
        if ss.empty:
            continue
        plt.figure(figsize=(7, 4.5))
        for alg in ALGO_ORDER:
            aa = ss[ss["algorithm"] == alg].sort_values("rate")
            if aa.empty:
                continue
            x = aa["rate"].to_numpy(dtype=float)
            y = aa["blocking_probability"].to_numpy(dtype=float)
            ci = aa["blocking_ci95"].to_numpy(dtype=float)
            plt.plot(x, y, marker="o", label=alg)
            plt.fill_between(x, y-ci, y+ci, alpha=0.15)
        plt.xlabel("Request rate (requests/s)")
        plt.ylabel("Blocking probability")
        plt.title(f"Blocking vs load — {topo}")
        plt.legend()
        plt.tight_layout()
        plt.savefig(out_dir / f"blocking_vs_load_{topo}_final.png", dpi=220)
        plt.close()

    for row in representative_rows:
        topo = row["topology"]
        rate = row["representative_rate"]
        ss = raw[(raw["topology"] == topo) & (raw["rate"] == rate) & (raw["blocked"] == 0)]
        if ss.empty:
            continue
        plt.figure(figsize=(7, 4.5))
        for alg in ALGO_ORDER:
            aa = ss[ss["algorithm"] == alg]["bottleneck_fidelity"].dropna()
            aa = aa[aa > 0].sort_values()
            if len(aa) == 0:
                continue
            y = np.arange(1, len(aa)+1) / len(aa)
            plt.plot(aa.to_numpy(dtype=float), y, label=alg)
        plt.xlabel("Bottleneck fidelity")
        plt.ylabel("CDF")
        plt.title(f"Fidelity CDF at representative load (rate={rate}) — {topo}")
        plt.legend()
        plt.tight_layout()
        plt.savefig(out_dir / f"fidelity_cdf_reprate_{topo}.png", dpi=220)
        plt.close()

    selected_topologies = [t for t in ["mesh16", "irregular12", "mesh9"] if t in set(raw["topology"].astype(str))]
    selected_algs = ["keyaware", "ga_tcheby_proxy"]
    link_heatmap_manifest = []
    for topo in selected_topologies:
        rate = select_representative_rate(summary, topo)
        if rate is None:
            continue
        for alg in selected_algs:
            mat = build_link_count_matrix(raw, topo, alg, rate)
            plt.figure(figsize=(5.2, 4.6))
            plt.imshow(mat, aspect="auto")
            plt.colorbar(label="Traversed link count")
            plt.xlabel("Destination node")
            plt.ylabel("Source node")
            plt.title(f"Per-link usage — {topo}, {alg}, rate={rate}")
            plt.tight_layout()
            out_name = f"perlink_usage_{topo}_{alg}_rate{rate}.png"
            plt.savefig(out_dir / out_name, dpi=220)
            plt.close()
            link_heatmap_manifest.append({
                "topology": topo,
                "algorithm": alg,
                "rate": rate,
                "figure": out_name
            })

    scale_rows = []
    for topo in [t for t in TOPO_ORDER if t in set(summary["topology"].astype(str))]:
        rate = select_representative_rate(summary, topo)
        if rate is None:
            continue
        ss = summary[(summary["topology"].astype(str) == topo) & (summary["rate"] == rate)]
        for _, r in ss.iterrows():
            scale_rows.append({
                "topology": topo,
                "nodes": TOPO_SIZE.get(topo, np.nan),
                "algorithm": str(r["algorithm"]),
                "representative_rate": rate,
                "blocking_probability": float(r["blocking_probability"]),
                "mean_bottleneck_fidelity": float(r["mean_bottleneck_fidelity"]),
            })
    scale_df = pd.DataFrame(scale_rows)
    if not scale_df.empty:
        scale_df.to_csv(out_dir / "omnet_scalability_selectedrate.csv", index=False)

        plt.figure(figsize=(7, 4.5))
        for alg in ["keyaware", "ga_tcheby_proxy"]:
            ss = scale_df[scale_df["algorithm"] == alg].sort_values("nodes")
            if ss.empty:
                continue
            plt.plot(ss["nodes"], ss["blocking_probability"], marker="o", label=alg)
        plt.xlabel("Topology size (nodes)")
        plt.ylabel("Blocking probability at representative load")
        plt.title("Scalability view — blocking")
        plt.legend()
        plt.tight_layout()
        plt.savefig(out_dir / "scalability_blocking_selectedrate.png", dpi=220)
        plt.close()

        plt.figure(figsize=(7, 4.5))
        for alg in ["keyaware", "ga_tcheby_proxy"]:
            ss = scale_df[scale_df["algorithm"] == alg].sort_values("nodes")
            if ss.empty:
                continue
            plt.plot(ss["nodes"], ss["mean_bottleneck_fidelity"], marker="o", label=alg)
        plt.xlabel("Topology size (nodes)")
        plt.ylabel("Mean bottleneck fidelity at representative load")
        plt.title("Scalability view — fidelity")
        plt.legend()
        plt.tight_layout()
        plt.savefig(out_dir / "scalability_fidelity_selectedrate.png", dpi=220)
        plt.close()

    paper_rows = []
    highlights = {"topology_highlights": [], "link_heatmap_manifest": link_heatmap_manifest}
    for topo in [t for t in TOPO_ORDER if t in set(summary["topology"].astype(str))]:
        rate = select_representative_rate(summary, topo)
        if rate is None:
            continue
        ss = summary[(summary["topology"].astype(str) == topo) & (summary["rate"] == rate)]
        for _, r in ss.iterrows():
            paper_rows.append({
                "topology": topo,
                "nodes": TOPO_SIZE.get(topo, np.nan),
                "representative_rate": rate,
                "algorithm": str(r["algorithm"]),
                "blocking_probability": float(r["blocking_probability"]),
                "blocking_ci95": float(r["blocking_ci95"]),
                "mean_bottleneck_fidelity": float(r["mean_bottleneck_fidelity"]),
                "fidelity_ci95": float(r["fidelity_ci95"]),
                "mean_hops": float(r["mean_hops"]),
                "mean_distance_km": float(r["mean_distance_km"]),
            })

        key = ss[ss["algorithm"] == "keyaware"]
        ga = ss[ss["algorithm"] == "ga_tcheby_proxy"]
        if not key.empty and not ga.empty:
            key = key.iloc[0]
            ga = ga.iloc[0]
            highlights["topology_highlights"].append({
                "topology": topo,
                "representative_rate": int(rate),
                "blocking_delta_ga_minus_keyaware": float(ga["blocking_probability"] - key["blocking_probability"]),
                "fidelity_delta_ga_minus_keyaware": float(ga["mean_bottleneck_fidelity"] - key["mean_bottleneck_fidelity"]),
                "hop_delta_ga_minus_keyaware": float(ga["mean_hops"] - key["mean_hops"]),
                "distance_delta_ga_minus_keyaware": float(ga["mean_distance_km"] - key["mean_distance_km"]),
            })

    paper_df = pd.DataFrame(paper_rows)
    if not paper_df.empty:
        paper_df.to_csv(out_dir / "omnet_paper_ready_table.csv", index=False)

    (out_dir / "omnet_final_highlights.json").write_text(json.dumps(highlights, indent=2), encoding="utf-8")

    md = []
    md.append("# QFlow OMNeT++ Refined Dynamic-Load Package\n\n")
    md.append("## Purpose\n")
    md.append("- This package is the refined dynamic-load evidence layer for the QFlow paper.\n")
    md.append("- It is intended to complement the existing hardware/timing section.\n")
    md.append("- Repetitions are now distinguished through explicit `rngSeed` overrides.\n\n")
    md.append("## Main outputs\n")
    md.append("- `omnet_final_summary.csv`\n")
    md.append("- `omnet_paper_ready_table.csv`\n")
    md.append("- `omnet_representative_rates.csv`\n")
    md.append("- `omnet_final_highlights.json`\n")
    md.append("- `blocking_vs_load_<topology>_final.png`\n")
    md.append("- `fidelity_cdf_reprate_<topology>.png`\n")
    md.append("- `perlink_usage_<topology>_<algorithm>_rate<r>.png`\n")
    md.append("- `scalability_blocking_selectedrate.png`\n")
    md.append("- `scalability_fidelity_selectedrate.png`\n")
    (out_dir / "README_omnet_final.md").write_text("".join(md), encoding="utf-8")

    print(f"Wrote {out_dir / 'omnet_final_summary.csv'}")
    print(f"Wrote {out_dir / 'omnet_paper_ready_table.csv'}")
    print(f"Wrote {out_dir / 'omnet_final_highlights.json'}")
    print(f"Wrote {out_dir / 'README_omnet_final.md'}")

if __name__ == "__main__":
    main()
