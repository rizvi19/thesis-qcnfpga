#!/usr/bin/env python3
"""
Extract FDPE-V0 Yosys synthesis summary into CSV.

Input:
  asic/fdpe_kernel/reports/fdpe_kernel_v0_yosys_synth.log

Output:
  asic/fdpe_kernel/results/fdpe_kernel_v0_yosys_summary.csv
"""

from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parents[3]
LOG = ROOT / "asic/fdpe_kernel/reports/fdpe_kernel_v0_yosys_synth.log"
OUT = ROOT / "asic/fdpe_kernel/results/fdpe_kernel_v0_yosys_summary.csv"

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

def main() -> None:
    text = LOG.read_text(errors="replace")

    row = {
        "kernel": "fdpe_kernel_v0",
        "lut_entries": 256,
        "fidelity_format": "Q0.16",
        "lut_source": "generated_exp_lut_256_hex",
        "synthesis_type": "yosys_generic",
        "memory_preserved": "no",
        "memory_mapping_note": "exp_lut mapped to FF/mux logic in generic Yosys run",
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
        row[cell.replace("$_", "").replace("_", "").lower()] = find_int(
            rf"{escaped}\s+(\d+)", text
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)

    print(f"[PASS] wrote {OUT}")
    print(f"total_cells={row['total_cells']}")
    print(f"memory_preserved={row['memory_preserved']}")
    print(row["memory_mapping_note"])

if __name__ == "__main__":
    main()
