#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def load_all(results_dir: Path) -> pd.DataFrame:
    frames = []
    for p in results_dir.glob("*.csv"):
        try:
            df = pd.read_csv(p)
            if not df.empty:
                df["source_file"] = p.name
                frames.append(df)
        except Exception as e:
            print(f"Skipping {p}: {e}")
    if not frames:
        raise SystemExit("No CSV files found.")
    return pd.concat(frames, ignore_index=True)

def main():
    if len(sys.argv) < 3:
        raise SystemExit("Usage: plot_qflow_omnet_results.py <results_dir> <out_dir>")
    results_dir = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_all(results_dir)

    blocking = df.groupby(["topology", "algorithm"], as_index=False)["blocked"].mean()
    plt.figure(figsize=(8,4.5))
    for alg, sub in blocking.groupby("algorithm"):
        sub = sub.sort_values("topology")
        x = range(len(sub))
        plt.plot(list(x), sub["blocked"], marker="o", label=alg)
    topo_labels = sorted(blocking["topology"].unique())
    plt.xticks(range(len(topo_labels)), topo_labels)
    plt.ylabel("Blocking probability")
    plt.xlabel("Topology")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "blocking_overview.png", dpi=200)
    plt.close()

    plt.figure(figsize=(7,4.5))
    for alg, sub in df[df["blocked"] == 0].groupby("algorithm"):
        vals = sub["bottleneck_fidelity"].dropna().sort_values().values
        if len(vals) == 0:
            continue
        y = [i / len(vals) for i in range(1, len(vals)+1)]
        plt.plot(vals, y, label=alg)
    plt.xlabel("Bottleneck fidelity")
    plt.ylabel("CDF")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "fidelity_cdf.png", dpi=200)
    plt.close()

    plt.figure(figsize=(8,4.5))
    order = sorted(df["algorithm"].unique())
    data = [df[df["algorithm"] == alg]["decision_latency_ms"].dropna().values for alg in order]
    plt.boxplot(data, labels=order, showfliers=False)
    plt.ylabel("Decision latency (ms)")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(out_dir / "latency_boxplot.png", dpi=200)
    plt.close()

    summary = df.groupby(["topology","algorithm"], as_index=False).agg(
        blocking_prob=("blocked","mean"),
        mean_fidelity=("bottleneck_fidelity","mean"),
        mean_distance=("distance_km","mean"),
        mean_latency_ms=("decision_latency_ms","mean"),
        mean_max_util=("max_utilization","mean"),
        requests=("request_id","count"),
    )
    summary.to_csv(out_dir / "summary_metrics.csv", index=False)
    print(f"Wrote plots and summary to {out_dir}")

if __name__ == "__main__":
    main()
