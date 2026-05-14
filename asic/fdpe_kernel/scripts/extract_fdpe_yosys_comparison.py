#!/usr/bin/env python3
"""
Extract FDPE Yosys synthesis summaries for all FDPE variants.

Outputs:
  asic/fdpe_kernel/results/fdpe_yosys_comparison.csv
"""

from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "asic/fdpe_kernel/results/fdpe_yosys_comparison.csv"

VARIANTS = [
    {
        "kernel": "fdpe_kernel_v0",
        "variant": "V0_256LUT_Q016",
        "lut_entries": 256,
        "index_bits": 8,
        "log": ROOT / "asic/fdpe_kernel/reports/fdpe_kernel_v0_yosys_synth.log",
        "memory_note": "exp_lut mapped to FF/mux logic",
    },
    {
        "kernel": "fdpe_kernel_v1_lut128",
        "variant": "V1_128LUT_Q016",
        "lut_entries": 128,
        "index_bits": 7,
        "log": ROOT / "asic/fdpe_kernel/reports/fdpe_kernel_v1_lut128_yosys_synth.log",
        "memory_note": "exp_lut mapped to FF/mux logic",
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
        "lut_entries": v["lut_entries"],
        "index_bits": v["index_bits"],
        "fidelity_format": "Q0.16",
        "synthesis_type": "yosys_generic",
        "memory_preserved": "no",
        "memory_mapping_note": v["memory_note"],
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
        delta = row["total_cells"] - baseline_cells
        reduction = (baseline_cells - row["total_cells"]) / baseline_cells * 100.0
        row["delta_cells_vs_v0"] = delta
        row["cell_reduction_percent_vs_v0"] = reduction

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
            f"delta_vs_v0={row['delta_cells_vs_v0']}, "
            f"reduction_vs_v0={row['cell_reduction_percent_vs_v0']:.2f}%"
        )


if __name__ == "__main__":
    main()
