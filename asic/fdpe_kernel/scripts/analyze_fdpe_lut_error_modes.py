#!/usr/bin/env python3
"""
Analyze FDPE LUT approximation error for floor lookup vs linear interpolation.

This script evaluates exp(-x) approximation over dense x samples.

Modes:
  1. floor lookup: use LUT[floor(x / step)]
  2. linear interpolation: interpolate between adjacent LUT entries

Outputs:
  asic/fdpe_kernel/results/fdpe_lut_error_modes_comparison.csv
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "asic/fdpe_kernel/results/fdpe_lut_error_modes_comparison.csv"

Q016_MAX = 65535
X_MAX = 8.0
SAMPLES = 200_000
LUT_ENTRIES_LIST = [256, 128, 64]


def q016_exp_value(x: float) -> int:
    return max(0, min(Q016_MAX, int(round(math.exp(-x) * Q016_MAX))))


def lut_value(entries: int, idx: int) -> float:
    idx = max(0, min(entries - 1, idx))
    x_idx = idx * X_MAX / entries
    q = q016_exp_value(x_idx)
    return q / Q016_MAX


def lookup_floor(x: float, entries: int) -> float:
    if x < 0:
        x = 0.0
    if x >= X_MAX:
        x = X_MAX - 1e-12

    idx = int(x * entries / X_MAX)
    return lut_value(entries, idx)


def lookup_linear(x: float, entries: int) -> float:
    if x < 0:
        x = 0.0
    if x >= X_MAX:
        x = X_MAX - 1e-12

    pos = x * entries / X_MAX
    idx = int(pos)
    frac = pos - idx

    if idx >= entries - 1:
        return lut_value(entries, entries - 1)

    y0 = lut_value(entries, idx)
    y1 = lut_value(entries, idx + 1)

    return y0 + frac * (y1 - y0)


def summarize(entries: int, mode: str) -> dict:
    if mode == "floor":
        fn = lookup_floor
    elif mode == "linear":
        fn = lookup_linear
    else:
        raise ValueError(mode)

    max_abs_all = 0.0
    max_rel_all = 0.0

    max_abs_0_3 = 0.0
    max_rel_0_3 = 0.0

    max_abs_0_5 = 0.0
    max_rel_0_5 = 0.0

    sum_abs_all = 0.0
    sum_rel_all = 0.0

    for n in range(SAMPLES):
        x = X_MAX * n / SAMPLES
        exact = math.exp(-x)
        approx = fn(x, entries)

        abs_err = abs(exact - approx)
        rel_err = abs_err / exact if exact > 0 else 0.0

        max_abs_all = max(max_abs_all, abs_err)
        max_rel_all = max(max_rel_all, rel_err)

        if x <= 3.0:
            max_abs_0_3 = max(max_abs_0_3, abs_err)
            max_rel_0_3 = max(max_rel_0_3, rel_err)

        if x <= 5.0:
            max_abs_0_5 = max(max_abs_0_5, abs_err)
            max_rel_0_5 = max(max_rel_0_5, rel_err)

        sum_abs_all += abs_err
        sum_rel_all += rel_err

    return {
        "lut_entries": entries,
        "mode": mode,
        "x_range": "[0,8)",
        "samples": SAMPLES,
        "max_abs_error_all": max_abs_all,
        "max_rel_error_all": max_rel_all,
        "max_abs_error_x0_3": max_abs_0_3,
        "max_rel_error_x0_3": max_rel_0_3,
        "max_abs_error_x0_5": max_abs_0_5,
        "max_rel_error_x0_5": max_rel_0_5,
        "mean_abs_error_all": sum_abs_all / SAMPLES,
        "mean_rel_error_all": sum_rel_all / SAMPLES,
    }


def main() -> None:
    rows = []
    for entries in LUT_ENTRIES_LIST:
        rows.append(summarize(entries, "floor"))
        rows.append(summarize(entries, "linear"))

    OUT.parent.mkdir(parents=True, exist_ok=True)

    headers = list(rows[0].keys())
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[PASS] wrote {OUT}")
    for row in rows:
        print(
            f"LUT{row['lut_entries']} {row['mode']}: "
            f"max_abs_all={row['max_abs_error_all']:.6e}, "
            f"max_rel_all={row['max_rel_error_all']:.6e}, "
            f"max_rel_x0_3={row['max_rel_error_x0_3']:.6e}"
        )


if __name__ == "__main__":
    main()
