#!/usr/bin/env python3
"""
Generate QFlow FDPE exp(-x) LUT for ASIC/VLSI kernel study.

LUT:
  - 256 entries
  - x in [0, 8), step = 8/256 = 1/32
  - output format: Q0.16 unsigned fixed-point
  - value = round(exp(-x) * 65535)

Outputs:
  - asic/fdpe_kernel/config/exp_lut_256.hex
  - asic/fdpe_kernel/results/exp_lut_256_summary.txt
"""

from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

OUT_HEX = ROOT / "asic/fdpe_kernel/config/exp_lut_256.hex"
OUT_SUMMARY = ROOT / "asic/fdpe_kernel/results/exp_lut_256_summary.txt"

LUT_ENTRIES = 256
X_MAX = 8.0
Q016_MAX = 65535


def q016_exp_value(x: float) -> int:
    value = int(round(math.exp(-x) * Q016_MAX))
    return max(0, min(Q016_MAX, value))


def main() -> None:
    OUT_HEX.parent.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)

    values = []
    max_abs_error = 0.0
    max_rel_error = 0.0

    for i in range(LUT_ENTRIES):
        x = i * X_MAX / LUT_ENTRIES
        q = q016_exp_value(x)
        approx = q / Q016_MAX
        exact = math.exp(-x)
        abs_error = abs(exact - approx)
        rel_error = abs_error / exact if exact != 0 else 0.0

        max_abs_error = max(max_abs_error, abs_error)
        max_rel_error = max(max_rel_error, rel_error)
        values.append(q)

    with OUT_HEX.open("w", encoding="utf-8") as f:
        for q in values:
            f.write(f"{q:04x}\n")

    with OUT_SUMMARY.open("w", encoding="utf-8") as f:
        f.write("QFlow FDPE exp(-x) LUT summary\n")
        f.write("================================\n")
        f.write(f"entries: {LUT_ENTRIES}\n")
        f.write(f"x_range: [0, {X_MAX})\n")
        f.write(f"step: {X_MAX / LUT_ENTRIES}\n")
        f.write("format: Q0.16 unsigned\n")
        f.write(f"scale: {Q016_MAX}\n")
        f.write(f"first_entry_hex: {values[0]:04x}\n")
        f.write(f"last_entry_hex: {values[-1]:04x}\n")
        f.write(f"max_abs_quantization_error: {max_abs_error:.12e}\n")
        f.write(f"max_rel_quantization_error: {max_rel_error:.12e}\n")

    print(f"[PASS] wrote {OUT_HEX}")
    print(f"[PASS] wrote {OUT_SUMMARY}")
    print(f"max_abs_quantization_error={max_abs_error:.12e}")
    print(f"max_rel_quantization_error={max_rel_error:.12e}")


if __name__ == "__main__":
    main()
