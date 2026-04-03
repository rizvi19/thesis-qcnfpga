#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

SRC = Path("results/paper/data/figures/fig03_blocking/source/omnet_paper_summary.csv")
OUT_PDF = Path("results/paper/export/pdf/qflow_fig03_blocking_main.pdf")
OUT_SVG = Path("results/paper/export/svg/qflow_fig03_blocking_main.svg")
OUT_PNG = Path("results/paper/export/png/qflow_fig03_blocking_main.png")

TOPOS = [("mesh16", "Mesh-16"), ("irregular12", "Irregular-12")]
DELTA_ALGOS = ["random", "ga_tcheby_proxy"]   # keep only informative differences
DELTA_LABELS = {
    "random": "Random − Key-aware",
    "ga_tcheby_proxy": "GA proxy − Key-aware",
}
DELTA_STYLES = {
    "random": dict(marker="^", linestyle="-.", linewidth=1.7, markersize=4.4),
    "ga_tcheby_proxy": dict(marker="D", linestyle=":", linewidth=1.9, markersize=4.2),
}

def main():
    if not SRC.exists():
        raise FileNotFoundError(f"Missing input CSV: {SRC}")

    df = pd.read_csv(SRC)
    required = {"topology", "algorithm", "rate", "blocking_probability"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df[df["topology"].astype(str).isin([t[0] for t in TOPOS])].copy()

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 9,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
    })

    fig, axes = plt.subplots(
        2, 2,
        figsize=(7.25, 4.8),
        sharex="col",
        gridspec_kw={"height_ratios": [3.0, 1.45]}
    )

    delta_handles = None
    delta_labels = None

    for col, (topo_key, topo_title) in enumerate(TOPOS):
        sub = df[df["topology"].astype(str) == topo_key].copy()
        if sub.empty:
            raise ValueError(f"No rows found for topology: {topo_key}")

        ax_top = axes[0, col]
        ax_bot = axes[1, col]

        # ---------- Top panel: common trend + min/max band ----------
        pivot = sub.pivot(index="rate", columns="algorithm", values="blocking_probability").sort_index()
        rates = pivot.index.to_numpy(dtype=float)

        y_min = pivot.min(axis=1).to_numpy(dtype=float)
        y_max = pivot.max(axis=1).to_numpy(dtype=float)
        y_ref = pivot["keyaware"].to_numpy(dtype=float) if "keyaware" in pivot.columns else pivot.mean(axis=1).to_numpy(dtype=float)

        ax_top.fill_between(rates, y_min, y_max, alpha=0.18)
        ax_top.plot(
            rates, y_ref,
            marker="o", linestyle="-", linewidth=2.0, markersize=5.0,
            label="Common blocking trend"
        )

        ax_top.set_title(topo_title, pad=7)
        ax_top.set_xlim(1.5, 41.5)
        ax_top.set_ylim(0.08, 0.95)
        ax_top.set_xticks([2, 5, 10, 20, 40])
        ax_top.grid(axis="y", alpha=0.25)
        ax_top.set_axisbelow(True)
        ax_top.spines["top"].set_visible(False)
        ax_top.spines["right"].set_visible(False)

        if col == 0:
            ax_top.set_ylabel("Blocking probability")

        ax_top.text(
            0.02, 0.98,
            f"({chr(ord('a') + col)})",
            transform=ax_top.transAxes,
            ha="left", va="top",
            fontsize=9, fontweight="bold"
        )

        ax_top.text(
            0.98, 0.06,
            "band = min–max across algorithms",
            transform=ax_top.transAxes,
            ha="right", va="bottom",
            fontsize=6.8
        )

        # ---------- Bottom panel: delta vs Key-aware ----------
        key_df = sub[sub["algorithm"].astype(str) == "keyaware"][["rate", "blocking_probability"]].rename(
            columns={"blocking_probability": "keyaware_bp"}
        ).sort_values("rate")

        all_delta_vals = []

        for alg in DELTA_ALGOS:
            ss = sub[sub["algorithm"].astype(str) == alg][["rate", "blocking_probability"]].sort_values("rate")
            if ss.empty:
                continue

            merged = ss.merge(key_df, on="rate", how="left")
            merged["delta_milli"] = (merged["blocking_probability"] - merged["keyaware_bp"]) * 1000.0
            all_delta_vals.extend(merged["delta_milli"].tolist())

            style = DELTA_STYLES.get(alg, {})
            h, = ax_bot.plot(
                merged["rate"],
                merged["delta_milli"],
                label=DELTA_LABELS.get(alg, alg),
                **style
            )

            if delta_handles is None:
                delta_handles, delta_labels = ax_bot.get_legend_handles_labels()

        ax_bot.axhline(0.0, color="black", linewidth=0.8, linestyle="--", alpha=0.65)
        ax_bot.set_xlim(1.5, 41.5)
        ax_bot.set_xticks([2, 5, 10, 20, 40])
        ax_bot.set_xlabel("Offered load (requests/s)")
        ax_bot.grid(axis="y", alpha=0.20)
        ax_bot.set_axisbelow(True)
        ax_bot.spines["top"].set_visible(False)
        ax_bot.spines["right"].set_visible(False)

        if col == 0:
            ax_bot.set_ylabel(r"$\Delta$ vs Key-aware" "\n" r"($\times 10^{-3}$)")

        if all_delta_vals:
            ymin = min(all_delta_vals)
            ymax = max(all_delta_vals)
            span = ymax - ymin
            pad = 0.25 * span if span > 0 else 0.4
            ax_bot.set_ylim(ymin - pad, ymax + pad)

        ax_bot.text(
            0.02, 0.92,
            f"({chr(ord('c') + col)})",
            transform=ax_bot.transAxes,
            ha="left", va="top",
            fontsize=9, fontweight="bold"
        )

    if delta_handles and delta_labels:
        fig.legend(
            delta_handles, delta_labels,
            loc="upper center",
            ncol=2,
            frameon=False,
            bbox_to_anchor=(0.5, 1.01)
        )

    fig.tight_layout(rect=(0, 0, 1, 0.94))

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
