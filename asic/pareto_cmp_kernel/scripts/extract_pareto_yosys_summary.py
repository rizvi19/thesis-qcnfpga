#!/usr/bin/env python3
"""
Extract Pareto comparator Yosys synthesis summary into CSV.

Output:
  asic/pareto_cmp_kernel/results/pareto_yosys_comparison.csv
"""

from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "asic/pareto_cmp_kernel/results/pareto_yosys_comparison.csv"

VARIANTS = [
    {
        "kernel": "pareto_cmp_c0_full",
        "variant": "C0_FULL_PARETO_COMPARATOR",
        "selector_model": "full_pareto_plus_tiebreak",
        "log": ROOT / "asic/pareto_cmp_kernel/reports/pareto_cmp_c0_full_yosys_synth.log",
        "note": "full metric dominance comparator with score/fidelity/key/hop/qber tie-breaks",
    },
    {
        "kernel": "pareto_cmp_c1_scorefirst",
        "variant": "C1_SCORE_FIRST_SELECTOR",
        "selector_model": "score_first_priority_selector",
        "log": ROOT / "asic/pareto_cmp_kernel/reports/pareto_cmp_c1_scorefirst_yosys_synth.log",
        "note": "priority selector: score, fidelity, key_count, hop_count, qber",
    },
]

CELL_TYPES = [
    "$_ANDNOT_",
    "$_AND_",
    "$_MUX_",
    "$_NAND_",
    "$_NOR_",
    "$_NOT_",
    "$_ORNOT_",
    "$_OR_",
    "$_SDFFE_PN0P_",
    "$_SDFF_PN0_",
    "$_SDFF_PP0_",
    "$_XNOR_",
    "$_XOR_",
]


def find_int(pattern: str, text: str, default: int = 0) -> int:
    m = re.search(pattern, text)
    return int(m.group(1)) if m else default


def parse_variant(v: dict) -> dict:
    text = v["log"].read_text(errors="replace")

    row = {
        "kernel": v["kernel"],
        "variant": v["variant"],
        "selector_model": v["selector_model"],
        "synthesis_type": "yosys_generic",
        "note": v["note"],
        "wires": find_int(r"Number of wires:\s+(\d+)", text),
        "wire_bits": find_int(r"Number of wire bits:\s+(\d+)", text),
        "public_wires": find_int(r"Number of public wires:\s+(\d+)", text),
        "public_wire_bits": find_int(r"Number of public wire bits:\s+(\d+)", text),
        "ports": find_int(r"Number of ports:\s+(\d+)", text),
        "port_bits": find_int(r"Number of port bits:\s+(\d+)", text),
        "memories": find_int(r"Number of memories:\s+(\d+)", text),
        "memory_bits": find_int(r"Number of memory bits:\s+(\d+)", text),
        "processes": find_int(r"Number of processes:\s+(\d+)", text),
        "total_cells": find_int(r"Number of cells:\s+(\d+)", text),
    }

    for cell in CELL_TYPES:
        escaped = re.escape(cell)
        key = cell.replace("$_", "").replace("_", "").lower()
        row[key] = find_int(rf"{escaped}\s+(\d+)", text)

    return row


def main() -> None:
    rows = [parse_variant(v) for v in VARIANTS]

    baseline_cells = rows[0]["total_cells"]
    for row in rows:
        row["delta_cells_vs_c0"] = row["total_cells"] - baseline_cells
        row["cell_reduction_percent_vs_c0"] = (
            (baseline_cells - row["total_cells"]) / baseline_cells * 100.0
            if baseline_cells else 0.0
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    headers = list(rows[0].keys())

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[PASS] wrote {OUT}")
    for row in rows:
        print(
            f"{row['variant']}: total_cells={row['total_cells']}, "
            f"delta_vs_c0={row['delta_cells_vs_c0']}, "
            f"reduction_vs_c0={row['cell_reduction_percent_vs_c0']:.2f}%"
        )


if __name__ == "__main__":
    main()
