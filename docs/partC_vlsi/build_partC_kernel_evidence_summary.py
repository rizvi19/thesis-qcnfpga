#!/usr/bin/env python3
"""
Build combined Part C kernel evidence summary.

Inputs:
  asic/fdpe_kernel/results/fdpe_yosys_comparison.csv
  asic/fdpe_kernel/results/fdpe_lut_error_modes_comparison.csv
  asic/skag_weight_kernel/results/skag_yosys_comparison.csv
  asic/pareto_cmp_kernel/results/pareto_yosys_comparison.csv

Outputs:
  results/partC_vlsi/partC_kernel_evidence_summary.csv
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FDPE_YOSYS = ROOT / "asic/fdpe_kernel/results/fdpe_yosys_comparison.csv"
FDPE_ERR = ROOT / "asic/fdpe_kernel/results/fdpe_lut_error_modes_comparison.csv"
SKAG_YOSYS = ROOT / "asic/skag_weight_kernel/results/skag_yosys_comparison.csv"
PARETO_YOSYS = ROOT / "asic/pareto_cmp_kernel/results/pareto_yosys_comparison.csv"

OUT = ROOT / "results/partC_vlsi/partC_kernel_evidence_summary.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def percent_str(x: float) -> str:
    return f"{x:.2f}%"


def main() -> None:
    rows = []

    # FDPE synthesis rows.
    fdpe_rows = read_csv(FDPE_YOSYS)
    fdpe_err_rows = read_csv(FDPE_ERR)

    # Map FDPE approximation errors by LUT/mode.
    err_map = {}
    for r in fdpe_err_rows:
        key = (r["lut_entries"], r["mode"])
        err_map[key] = r

    fdpe_mode_map = {
        "V0_256LUT_Q016": ("256", "floor"),
        "V1_128LUT_Q016_FLOOR": ("128", "floor"),
        "V2_128LUT_Q016_LINEAR_INTERP": ("128", "linear"),
        "V3_64LUT_Q016_LINEAR_INTERP": ("64", "linear"),
    }

    for r in fdpe_rows:
        variant = r["variant"]
        lut, mode = fdpe_mode_map.get(variant, ("", ""))
        err = err_map.get((lut, mode), {})

        rows.append({
            "kernel_family": "FDPE",
            "variant": variant,
            "design_role": "fidelity_decay_approximation",
            "total_cells": r["total_cells"],
            "baseline": "FDPE-V0",
            "delta_vs_baseline_cells": r["delta_cells_vs_v0"],
            "cell_reduction_vs_baseline_percent": percent_str(float(r["cell_reduction_percent_vs_v0"])),
            "accuracy_or_behavior": (
                f"max_rel_error_x0_3={float(err.get('max_rel_error_x0_3', 0.0)) * 100:.4f}%"
                if err else ""
            ),
            "main_interpretation": "area-accuracy LUT/interpolation tradeoff",
        })

    # SKAG rows.
    for r in read_csv(SKAG_YOSYS):
        behavior = "same tested scores as W0" if r["variant"] == "W1_FIXED_ALPHA_SHIFTADD" else "baseline tested scores"
        rows.append({
            "kernel_family": "SKAG",
            "variant": r["variant"],
            "design_role": "edge_weight_score",
            "total_cells": r["total_cells"],
            "baseline": "SKAG-W0",
            "delta_vs_baseline_cells": r["delta_cells_vs_w0"],
            "cell_reduction_vs_baseline_percent": percent_str(float(r["cell_reduction_percent_vs_w0"])),
            "accuracy_or_behavior": behavior,
            "main_interpretation": "fixed shift-add weights remove runtime multipliers",
        })

    # Pareto rows.
    for r in read_csv(PARETO_YOSYS):
        rows.append({
            "kernel_family": "Pareto",
            "variant": r["variant"],
            "design_role": "route_candidate_selection",
            "total_cells": r["total_cells"],
            "baseline": "Pareto-C0",
            "delta_vs_baseline_cells": r["delta_cells_vs_c0"],
            "cell_reduction_vs_baseline_percent": percent_str(float(r["cell_reduction_percent_vs_c0"])),
            "accuracy_or_behavior": "selection testbench passed",
            "main_interpretation": "full comparator already compact; score-first saves modest area",
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "kernel_family",
        "variant",
        "design_role",
        "total_cells",
        "baseline",
        "delta_vs_baseline_cells",
        "cell_reduction_vs_baseline_percent",
        "accuracy_or_behavior",
        "main_interpretation",
    ]

    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[PASS] wrote {OUT}")
    for r in rows:
        print(
            f"{r['kernel_family']:7s} {r['variant']:35s} "
            f"cells={r['total_cells']:>5s} "
            f"reduction={r['cell_reduction_vs_baseline_percent']}"
        )


if __name__ == "__main__":
    main()
