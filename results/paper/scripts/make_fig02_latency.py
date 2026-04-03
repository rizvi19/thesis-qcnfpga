#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path("results/paper/data/figures/fig02_latency")
SRC = ROOT / "source" / "latency_summary.csv"

OUT_PDF = Path("results/paper/export/pdf/qflow_fig02_latency_main.pdf")
OUT_SVG = Path("results/paper/export/svg/qflow_fig02_latency_main.svg")
OUT_PNG = Path("results/paper/export/png/qflow_fig02_latency_main.png")

ORDER = ["qflow_hw", "distance_sw", "keyaware_sw", "pmo_ga_sw"]


def main():
    if not SRC.exists():
        raise FileNotFoundError(f"Missing input CSV: {SRC}")

    df = pd.read_csv(SRC)

    required = [
        "method_id", "display_name", "domain", "latency_value",
        "latency_unit", "quantity_type", "source_basis",
        "include_in_main_plot", "notes"
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    plot_df = df[df["include_in_main_plot"].astype(str).str.lower() == "yes"].copy()
    plot_df["latency_value"] = plot_df["latency_value"].astype(float)

    units = plot_df["latency_unit"].dropna().astype(str).str.strip().unique().tolist()
    if len(units) != 1:
        raise ValueError(f"Expected exactly one common latency unit, found: {units}")
    unit = units[0]

    plot_df["order_key"] = plot_df["method_id"].apply(
        lambda x: ORDER.index(x) if x in ORDER else 999
    )
    plot_df = plot_df.sort_values("order_key").reset_index(drop=True)

    values = plot_df["latency_value"].tolist()
    labels = plot_df["display_name"].tolist()

    # Publication-style defaults
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 9,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 9,
        "figure.dpi": 150,
        "savefig.dpi": 600,
    })

    fig, ax = plt.subplots(figsize=(7.0, 2.9))

    y = list(range(len(plot_df)))
    bars = ax.barh(y, values)

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()

    ax.set_xscale("log")
    ax.set_xlabel(f"Decision latency ({unit}, log scale)")
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    # Clean spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Axis limits with padding
    xmin = min(values) / 1.8
    xmax = max(values) * 2.2
    ax.set_xlim(xmin, xmax)

    # Value annotations
    for yi, val in zip(y, values):
        if val < 1.0:
            txt = f"{val:.3f} μs"
        elif val < 10.0:
            txt = f"{val:.3f} μs"
        elif val < 100.0:
            txt = f"{val:.2f} μs"
        else:
            txt = f"{val:.2f} μs"
        ax.text(val * 1.10, yi, txt, va="center", ha="left", fontsize=8)

    fig.tight_layout()

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    OUT_SVG.parent.mkdir(parents=True, exist_ok=True)
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(OUT_PDF, bbox_inches="tight")
    fig.savefig(OUT_SVG, bbox_inches="tight")
    fig.savefig(OUT_PNG, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote {OUT_PDF}")
    print(f"Wrote {OUT_SVG}")
    print(f"Wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
