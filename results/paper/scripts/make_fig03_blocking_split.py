#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

SRC = Path("results/paper/data/figures/fig03_blocking/source/omnet_paper_summary.csv")

OUT1_PDF = Path("results/paper/export/pdf/qflow_fig03a_blocking_absolute.pdf")
OUT1_PNG = Path("results/paper/export/png/qflow_fig03a_blocking_absolute.png")

OUT2_PDF = Path("results/paper/export/pdf/qflow_fig03b_blocking_delta.pdf")
OUT2_PNG = Path("results/paper/export/png/qflow_fig03b_blocking_delta.png")

TOPOS = [("mesh16", "Mesh-16"), ("irregular12", "Irregular-12")]
ALGO_ORDER = ["distance", "keyaware", "random", "ga_tcheby_proxy"]
ALGO_LABELS = {
    "distance": "Distance",
    "keyaware": "Key-aware",
    "random": "Random",
    "ga_tcheby_proxy": "GA proxy",
}
ALGO_STYLES = {
    "distance":        dict(marker="o", linestyle="-",  linewidth=1.8, markersize=4.6),
    "keyaware":        dict(marker="s", linestyle="--", linewidth=1.8, markersize=4.6),
    "random":          dict(marker="^", linestyle="-.", linewidth=1.8, markersize=4.6),
    "ga_tcheby_proxy": dict(marker="D", linestyle=":",  linewidth=1.9, markersize=4.4),
}
DELTA_ALGOS = ["random", "ga_tcheby_proxy"]
DELTA_LABELS = {
    "random": "Random − Key-aware",
    "ga_tcheby_proxy": "GA proxy − Key-aware",
}
DELTA_STYLES = {
    "random": dict(marker="^", linestyle="-.", linewidth=1.7, markersize=4.4),
    "ga_tcheby_proxy": dict(marker="D", linestyle=":", linewidth=1.9, markersize=4.2),
}

def common_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 9,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
    })

def make_absolute(df: pd.DataFrame):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)

    for idx, (ax, (topo_key, topo_title)) in enumerate(zip(axes, TOPOS)):
        sub = df[df["topology"].astype(str) == topo_key].copy()
        pivot = sub.pivot(index="rate", columns="algorithm", values="blocking_probability").sort_index()

        rates = pivot.index.to_numpy(dtype=float)
        y_min = pivot.min(axis=1).to_numpy(dtype=float)
        y_max = pivot.max(axis=1).to_numpy(dtype=float)
        y_ref = pivot["keyaware"].to_numpy(dtype=float) if "keyaware" in pivot.columns else pivot.mean(axis=1).to_numpy(dtype=float)

        ax.fill_between(rates, y_min, y_max, alpha=0.18)
        ax.plot(
            rates, y_ref,
            marker="o", linestyle="-", linewidth=2.0, markersize=5.0
        )

        ax.set_title(topo_title, pad=7)
        ax.set_xlim(1.5, 41.5)
        ax.set_ylim(0.08, 0.95)
        ax.set_xticks([2, 5, 10, 20, 40])
        ax.set_xlabel("Offered load (requests/s)")
        if idx == 0:
            ax.set_ylabel("Blocking probability")

        ax.grid(axis="y", alpha=0.25)
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.text(
            0.02, 0.98,
            f"({chr(ord('a') + idx)})",
            transform=ax.transAxes,
            ha="left", va="top",
            fontsize=9, fontweight="bold"
        )

        ax.text(
            0.98, 0.06,
            "band = min–max across algorithms",
            transform=ax.transAxes,
            ha="right", va="bottom",
            fontsize=6.8
        )

    fig.tight_layout()
    OUT1_PDF.parent.mkdir(parents=True, exist_ok=True)
    OUT1_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT1_PDF, bbox_inches="tight")
    fig.savefig(OUT1_PNG, bbox_inches="tight", dpi=600)
    plt.close(fig)

def make_delta(df: pd.DataFrame):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.5), sharey=False)

    handles = None
    labels = None

    for idx, (ax, (topo_key, topo_title)) in enumerate(zip(axes, TOPOS)):
        sub = df[df["topology"].astype(str) == topo_key].copy()

        key_df = sub[sub["algorithm"].astype(str) == "keyaware"][["rate", "blocking_probability"]].rename(
            columns={"blocking_probability": "keyaware_bp"}
        ).sort_values("rate")

        all_delta_vals = []

        for alg in DELTA_ALGOS:
            ss = sub[sub["algorithm"].astype(str) == alg][["rate", "blocking_probability"]].sort_values("rate")
            merged = ss.merge(key_df, on="rate", how="left")
            merged["delta_milli"] = (merged["blocking_probability"] - merged["keyaware_bp"]) * 1000.0
            all_delta_vals.extend(merged["delta_milli"].tolist())

            h, = ax.plot(
                merged["rate"],
                merged["delta_milli"],
                label=DELTA_LABELS[alg],
                **DELTA_STYLES[alg]
            )
            if handles is None:
                handles, labels = ax.get_legend_handles_labels()

        ax.axhline(0.0, color="black", linewidth=0.8, linestyle="--", alpha=0.65)
        ax.set_title(topo_title, pad=7)
        ax.set_xlim(1.5, 41.5)
        ax.set_xticks([2, 5, 10, 20, 40])
        ax.set_xlabel("Offered load (requests/s)")
        ax.grid(axis="y", alpha=0.20)
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        if idx == 0:
            ax.set_ylabel(r"$\Delta$ vs Key-aware" "\n" r"($\times 10^{-3}$)")

        if all_delta_vals:
            ymin = min(all_delta_vals)
            ymax = max(all_delta_vals)
            span = ymax - ymin
            pad = 0.25 * span if span > 0 else 0.4
            ax.set_ylim(ymin - pad, ymax + pad)

        ax.text(
            0.02, 0.98,
            f"({chr(ord('c') + idx)})",
            transform=ax.transAxes,
            ha="left", va="top",
            fontsize=9, fontweight="bold"
        )

    if handles and labels:
        fig.legend(
            handles, labels,
            loc="upper center",
            ncol=2,
            frameon=False,
            bbox_to_anchor=(0.5, 1.02)
        )

    fig.tight_layout(rect=(0, 0, 1, 0.90))
    OUT2_PDF.parent.mkdir(parents=True, exist_ok=True)
    OUT2_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT2_PDF, bbox_inches="tight")
    fig.savefig(OUT2_PNG, bbox_inches="tight", dpi=600)
    plt.close(fig)

def main():
    if not SRC.exists():
        raise FileNotFoundError(f"Missing input CSV: {SRC}")

    df = pd.read_csv(SRC)
    required = {"topology", "algorithm", "rate", "blocking_probability"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df[df["topology"].astype(str).isin([t[0] for t in TOPOS])].copy()

    common_style()
    make_absolute(df)
    make_delta(df)

    print(f"Wrote {OUT1_PDF}")
    print(f"Wrote {OUT1_PNG}")
    print(f"Wrote {OUT2_PDF}")
    print(f"Wrote {OUT2_PNG}")

if __name__ == "__main__":
    main()
