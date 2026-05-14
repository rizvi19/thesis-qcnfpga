#!/usr/bin/env python3
"""
Generate QFlow FDPE exp(-x) LUTs for ASIC/VLSI kernel study.

Generated LUTs:
  - 256 entries, Q0.16
  - 128 entries, Q0.16

x range:
  [0, 8)

value:
  round(exp(-x) * 65535)
"""

from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
Q016_MAX = 65535
X_MAX = 8.0

LUT_CONFIGS = [
    (256, ROOT / "asic/fdpe_kernel/config/exp_lut_256.hex"),
    (128, ROOT / "asic/fdpe_kernel/config/exp_lut_128.hex"),
    (64, ROOT / "asic/fdpe_kernel/config/exp_lut_64.hex"),
]

OUT_SUMMARY = ROOT / "asic/fdpe_kernel/results/exp_lut_summary.csv"


def q016_exp_value(x: float) -> int:
    value = int(round(math.exp(-x) * Q016_MAX))
    return max(0, min(Q016_MAX, value))


def generate_lut(entries: int, out_hex: Path) -> dict:
    values = []
    max_abs_error = 0.0
    max_rel_error = 0.0

    # Operational range summaries
    range_stats = {
        "max_abs_error_x0_3": 0.0,
        "max_rel_error_x0_3": 0.0,
        "max_abs_error_x0_5": 0.0,
        "max_rel_error_x0_5": 0.0,
    }

    for i in range(entries):
        x = i * X_MAX / entries
        q = q016_exp_value(x)
        approx = q / Q016_MAX
        exact = math.exp(-x)
        abs_error = abs(exact - approx)
        rel_error = abs_error / exact if exact != 0 else 0.0

        max_abs_error = max(max_abs_error, abs_error)
        max_rel_error = max(max_rel_error, rel_error)

        if x <= 3.0:
            range_stats["max_abs_error_x0_3"] = max(range_stats["max_abs_error_x0_3"], abs_error)
            range_stats["max_rel_error_x0_3"] = max(range_stats["max_rel_error_x0_3"], rel_error)

        if x <= 5.0:
            range_stats["max_abs_error_x0_5"] = max(range_stats["max_abs_error_x0_5"], abs_error)
            range_stats["max_rel_error_x0_5"] = max(range_stats["max_rel_error_x0_5"], rel_error)

        values.append(q)

    out_hex.parent.mkdir(parents=True, exist_ok=True)
    with out_hex.open("w", encoding="utf-8") as f:
        for q in values:
            f.write(f"{q:04x}\n")

    return {
        "entries": entries,
        "hex_file": str(out_hex.relative_to(ROOT)),
        "x_range": "[0,8)",
        "step": X_MAX / entries,
        "format": "Q0.16",
        "scale": Q016_MAX,
        "first_entry_hex": f"{values[0]:04x}",
        "last_entry_hex": f"{values[-1]:04x}",
        "max_abs_quantization_error": max_abs_error,
        "max_rel_quantization_error": max_rel_error,
        **range_stats,
    }


def main() -> None:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    rows = []

    for entries, out_hex in LUT_CONFIGS:
        row = generate_lut(entries, out_hex)
        rows.append(row)
        print(f"[PASS] wrote {out_hex}")
        print(f"entries={entries}")
        print(f"max_abs_quantization_error={row['max_abs_quantization_error']:.12e}")
        print(f"max_rel_quantization_error={row['max_rel_quantization_error']:.12e}")

    headers = list(rows[0].keys())
    with OUT_SUMMARY.open("w", encoding="utf-8") as f:
        f.write(",".join(headers) + "\n")
        for row in rows:
            f.write(",".join(str(row[h]) for h in headers) + "\n")

    # Backward-compatible text summary for 256-entry baseline.
    old_summary = ROOT / "asic/fdpe_kernel/results/exp_lut_256_summary.txt"
    row256 = rows[0]
    with old_summary.open("w", encoding="utf-8") as f:
        f.write("QFlow FDPE exp(-x) LUT summary\n")
        f.write("================================\n")
        for k, v in row256.items():
            f.write(f"{k}: {v}\n")

    print(f"[PASS] wrote {OUT_SUMMARY}")
    print(f"[PASS] wrote {old_summary}")


if __name__ == "__main__":
    main()
