#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

SRC = Path("results/paper/data/figures/fig04_fidelity_cdf/source/omnet_run_level_summary.csv")
OUT_PDF = Path("results/paper/export/pdf/qflow_fig04_fidelity_cdf_main.pdf")
OUT_SVG = Path("results/paper/export/svg/qflow_fig04_fidelity_cdf_main.svg")
OUT_PNG = Path("results/paper/export/png/qflow_fig04_fidelity_cdf_main.png")

RATE = 40
TOPOS = [("mesh16", "Mesh-16"), ("irregular12", "Irregular-12")]
ALGO_ORDER = ["distance", "keyaware", "random", "ga_tcheby_proxy"]
ALGO_LABELS = {
    "distance": "Distance",
    "keyaware": "Key-aware",
    "random": "Random",
    "ga_tcheby_proxy": "GA proxy",
}

def main():
    if not SRC.exists():
        raise FileNotFoundError(f"Missing input CSV: {SRC}")

    df = pd.read_csv(SRC)
    required = {"topology", "algorithm", "rate", "mean_bottleneck_fidelity"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df[(df["topology"].isin([t[0] for t in TOPOS])) & (df["rate"] == RATE)].copy()

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 9,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
    })

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.15), sharey=True)

    for idx, (ax, (topo_key, topo_title)) in enumerate(zip(axes, TOPOS)):
        sub = df[df["topology"] == topo_key].copy()
        if sub.empty:
            raise ValueError(f"No rows found for topology {topo_key} at rate {RATE}")

        for alg in ALGO_ORDER:
            ss = sub[sub["algorithm"] == alg].copy()
            if ss.empty:
                continue
            vals = np.sort(ss["mean_bottleneck_fidelity"].to_numpy(dtype=float))
            y = np.arange(1, len(vals) + 1) / len(vals)
            ax.step(
                vals, y, where="post",
                label=ALGO_LABELS.get(alg, alg),
                linewidth=1.8
            )

        ax.set_title(topo_title, pad=7)
        ax.set_xlabel("Mean bottleneck fidelity")
        if idx == 0:
            ax.set_ylabel("ECDF across seeds")

        ax.grid(axis="y", alpha=0.25)
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    # collect the full legend after all curves are drawn
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=4,
        frameon=False,
        bbox_to_anchor=(0.5, 1.02)
    )

    fig.tight_layout(rect=(0, 0, 1, 0.90))

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    OUT_SVG.parent.mkdir(parents=True, exist_ok=True)
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(OUT_PDF, bbox_inches="tight")
    fig.savefig(OUT_SVG, bbox_inches="tight")
    fig.savefig(OUT_PNG, bbox_inches="tight", dpi=600)
    plt.close(fig)

    print(f"Wrote {OUT_PDF}")
    print(f"Wrote {OUT_SVG}")
    print(f"Wrote {OUT_PNG}")

if __name__ == "__main__":
    main()
