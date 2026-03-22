#!/usr/bin/env python3
from __future__ import annotations
import re
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

RESULT_PATTERN = re.compile(r'(?P<topology>[^_]+)_(?P<algorithm>.+)_rate(?P<rate>\d+)_seed(?P<seed>\d+)\.csv$')

ALGO_ORDER = ["distance", "keyaware", "random", "ga_tcheby_proxy"]
TOPO_ORDER = ["mesh9", "mesh16", "irregular12", "ring6"]

def parse_file_meta(path: Path):
    m = RESULT_PATTERN.match(path.name)
    if not m:
        return None
    d = m.groupdict()
    d["rate"] = int(d["rate"])
    d["seed"] = int(d["seed"])
    return d

def load_runs(results_dir: Path) -> pd.DataFrame:
    frames = []
    for p in sorted(results_dir.glob("*.csv")):
        meta = parse_file_meta(p)
        if not meta:
            continue
        df = pd.read_csv(p)
        if df.empty:
            continue
        for k, v in meta.items():
            df[k] = v
        frames.append(df)
    if not frames:
        raise SystemExit(f"No matching run CSV files found in {results_dir}")
    return pd.concat(frames, ignore_index=True)

def ci95(series: pd.Series) -> float:
    x = series.dropna().astype(float)
    if len(x) <= 1:
        return 0.0
    return 1.96 * x.std(ddof=1) / np.sqrt(len(x))

def main():
    import sys
    if len(sys.argv) < 3:
        raise SystemExit("Usage: make_qflow_omnet_paper_figures.py <results_dir> <out_dir>")
    results_dir = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    raw = load_runs(results_dir)

    grouped = raw.groupby(["topology","algorithm","rate","seed"], as_index=False).agg(
        blocking_probability=("blocked","mean"),
        mean_bottleneck_fidelity=("bottleneck_fidelity", lambda s: float(pd.Series(s)[pd.Series(s) > 0].mean()) if (pd.Series(s) > 0).any() else 0.0),
        mean_distance_km=("distance_km","mean"),
        mean_hops=("hops","mean"),
        mean_max_utilization=("max_utilization","mean"),
        mean_decision_latency_ms=("decision_latency_ms","mean"),
        requests=("request_id","count"),
        served=("blocked", lambda s: int((1-pd.Series(s)).sum())),
        blocked=("blocked", "sum"),
    )

    summary = grouped.groupby(["topology","algorithm","rate"], as_index=False).agg(
        blocking_probability=("blocking_probability","mean"),
        blocking_ci95=("blocking_probability", ci95),
        mean_bottleneck_fidelity=("mean_bottleneck_fidelity","mean"),
        fidelity_ci95=("mean_bottleneck_fidelity", ci95),
        mean_max_utilization=("mean_max_utilization","mean"),
        util_ci95=("mean_max_utilization", ci95),
        mean_decision_latency_ms=("mean_decision_latency_ms","mean"),
        latency_ci95=("mean_decision_latency_ms", ci95),
        mean_hops=("mean_hops","mean"),
        mean_distance_km=("mean_distance_km","mean"),
        total_runs=("seed","count"),
    )

    summary["algorithm"] = pd.Categorical(summary["algorithm"], categories=ALGO_ORDER, ordered=True)
    summary["topology"] = pd.Categorical(summary["topology"], categories=TOPO_ORDER, ordered=True)
    summary = summary.sort_values(["topology","rate","algorithm"]).reset_index(drop=True)

    grouped.to_csv(out_dir / "omnet_run_level_summary.csv", index=False)
    summary.to_csv(out_dir / "omnet_paper_summary.csv", index=False)

    # Figure 1: blocking vs request rate per topology
    for topo in [t for t in TOPO_ORDER if t in summary["topology"].astype(str).tolist()]:
        sub = summary[summary["topology"].astype(str) == topo]
        if sub.empty:
            continue
        plt.figure(figsize=(7,4.5))
        for alg in ALGO_ORDER:
            ss = sub[sub["algorithm"] == alg].sort_values("rate")
            if ss.empty:
                continue
            plt.plot(ss["rate"], ss["blocking_probability"], marker="o", label=alg)
            plt.fill_between(ss["rate"],
                             ss["blocking_probability"] - ss["blocking_ci95"],
                             ss["blocking_probability"] + ss["blocking_ci95"],
                             alpha=0.15)
        plt.xlabel("Request rate (requests/s)")
        plt.ylabel("Blocking probability")
        plt.title(f"Blocking vs load — {topo}")
        plt.legend()
        plt.tight_layout()
        plt.savefig(out_dir / f"blocking_vs_load_{topo}.png", dpi=220)
        plt.close()

    # Figure 2: fidelity CDF for highest rate of each topology
    for topo in sorted(raw["topology"].astype(str).unique()):
        sub = raw[(raw["topology"].astype(str) == topo)]
        if sub.empty:
            continue
        max_rate = sub["rate"].max()
        sub = sub[(sub["rate"] == max_rate) & (sub["blocked"] == 0)]
        plt.figure(figsize=(7,4.5))
        for alg in ALGO_ORDER:
            ss = sub[sub["algorithm"] == alg]["bottleneck_fidelity"].dropna()
            ss = ss[ss > 0].sort_values()
            if len(ss) == 0:
                continue
            y = np.arange(1, len(ss)+1) / len(ss)
            plt.plot(ss, y, label=alg)
        plt.xlabel("Bottleneck fidelity")
        plt.ylabel("CDF")
        plt.title(f"Fidelity CDF at highest load — {topo}")
        plt.legend()
        plt.tight_layout()
        plt.savefig(out_dir / f"fidelity_cdf_highload_{topo}.png", dpi=220)
        plt.close()

    # Figure 3: utilization heatmap for highest rate of each topology
    for topo in sorted(summary["topology"].astype(str).unique()):
        sub = summary[(summary["topology"].astype(str) == topo)]
        if sub.empty:
            continue
        max_rate = sub["rate"].max()
        sub = sub[sub["rate"] == max_rate].copy()
        if sub.empty:
            continue
        sub["algorithm"] = sub["algorithm"].astype(str)
        pivot = sub.pivot(index="algorithm", columns="rate", values="mean_max_utilization")
        if not pivot.empty:
            plt.figure(figsize=(4.2,3.2))
            plt.imshow(pivot.values, aspect="auto")
            plt.yticks(range(len(pivot.index)), list(pivot.index))
            plt.xticks(range(len(pivot.columns)), [str(x) for x in pivot.columns])
            plt.colorbar(label="Mean max utilization")
            plt.title(f"Utilization heatmap — {topo}")
            plt.tight_layout()
            plt.savefig(out_dir / f"utilization_heatmap_{topo}.png", dpi=220)
            plt.close()

    # Figure 4: scalability snapshot using highest-rate keyaware/ga comparison
    scale_rows = []
    topo_size = {"mesh9": 9, "mesh16": 16, "irregular12": 12, "ring6": 6}
    for topo in sorted(summary["topology"].astype(str).unique()):
        ss = summary[summary["topology"].astype(str) == topo]
        if ss.empty:
            continue
        max_rate = ss["rate"].max()
        ss = ss[(ss["rate"] == max_rate) & (ss["algorithm"].isin(["keyaware","ga_tcheby_proxy"]))]
        for _, row in ss.iterrows():
            scale_rows.append({
                "topology": topo,
                "nodes": topo_size.get(topo, np.nan),
                "algorithm": str(row["algorithm"]),
                "blocking_probability": row["blocking_probability"],
                "mean_bottleneck_fidelity": row["mean_bottleneck_fidelity"],
            })
    scale_df = pd.DataFrame(scale_rows)
    if not scale_df.empty:
        plt.figure(figsize=(7,4.5))
        for alg in ["keyaware","ga_tcheby_proxy"]:
            ss = scale_df[scale_df["algorithm"] == alg].sort_values("nodes")
            if ss.empty:
                continue
            plt.plot(ss["nodes"], ss["blocking_probability"], marker="o", label=f"{alg} blocking")
        plt.xlabel("Topology size (nodes)")
        plt.ylabel("Blocking probability at highest tested load")
        plt.title("Scalability snapshot")
        plt.legend()
        plt.tight_layout()
        plt.savefig(out_dir / "scalability_snapshot.png", dpi=220)
        plt.close()
        scale_df.to_csv(out_dir / "scalability_snapshot.csv", index=False)

    md = []
    md.append("# QFlow OMNeT++ Paper-Preliminary Summary\n\n")
    md.append("## What these results are for\n")
    md.append("- Dynamic-load network-level evidence for the paper.\n")
    md.append("- These runs complement the hardware timing/evaluation package; they do not replace it.\n\n")
    md.append("## Main outputs\n")
    md.append("- `omnet_paper_summary.csv`: aggregated table by topology, algorithm, and rate.\n")
    md.append("- `blocking_vs_load_<topology>.png`: blocking probability vs request rate.\n")
    md.append("- `fidelity_cdf_highload_<topology>.png`: fidelity CDF at highest tested load.\n")
    md.append("- `utilization_heatmap_<topology>.png`: utilization snapshot heatmap.\n")
    md.append("- `scalability_snapshot.png`: node-count scalability snapshot.\n")
    (out_dir / "README_paper_prelim.md").write_text("".join(md), encoding="utf-8")

    highlights = {"topology_highlights": []}
    for topo in sorted(summary["topology"].astype(str).unique()):
        ss = summary[summary["topology"].astype(str) == topo]
        if ss.empty:
            continue
        max_rate = ss["rate"].max()
        sr = ss[ss["rate"] == max_rate]
        key = sr[sr["algorithm"] == "keyaware"]
        ga = sr[sr["algorithm"] == "ga_tcheby_proxy"]
        if not key.empty and not ga.empty:
            key = key.iloc[0]
            ga = ga.iloc[0]
            highlights["topology_highlights"].append({
                "topology": topo,
                "highest_rate": int(max_rate),
                "blocking_delta_ga_minus_keyaware": float(ga["blocking_probability"] - key["blocking_probability"]),
                "fidelity_delta_ga_minus_keyaware": float(ga["mean_bottleneck_fidelity"] - key["mean_bottleneck_fidelity"]),
                "utilization_delta_ga_minus_keyaware": float(ga["mean_max_utilization"] - key["mean_max_utilization"]),
                "latency_delta_ga_minus_keyaware_ms": float(ga["mean_decision_latency_ms"] - key["mean_decision_latency_ms"]),
            })
    (out_dir / "omnet_paper_highlights.json").write_text(json.dumps(highlights, indent=2), encoding="utf-8")

    print(f"Wrote {out_dir / 'omnet_paper_summary.csv'}")
    print(f"Wrote {out_dir / 'README_paper_prelim.md'}")
    print(f"Wrote {out_dir / 'omnet_paper_highlights.json'}")

if __name__ == "__main__":
    main()
