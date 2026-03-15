#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

FID_SCALE = 65535
X_SCALE = 1 << 13  # Q4.13


def float_to_q016(x: float) -> int:
    x = max(0.0, min(1.0, x))
    return int(round(x * FID_SCALE))


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert FDPE golden CSV into packed memh vectors.")
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    rows = []
    with args.csv.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_id = int(row["case_id"])
            t_s = float(row["t_s"])
            t0_s = float(row["t0_s"])
            tau_s = float(row["tau_s"])
            f_init = float(row["f_init"])
            expected = int(row["lut_q016"])

            if tau_s <= 0:
                x_norm = 8.0
            else:
                x_norm = (t_s - t0_s) / tau_s
            if x_norm < 0:
                x_norm = 0.0
            # keep exact endpoint distinguishable
            x_q4_13 = int(round(x_norm * X_SCALE))
            if x_q4_13 > ((16 << 13) - 1):
                x_q4_13 = (16 << 13) - 1

            f_init_q016 = float_to_q016(f_init)
            packed = ((case_id & 0xFF) << 49) | ((x_q4_13 & 0x1FFFF) << 32) | ((f_init_q016 & 0xFFFF) << 16) | (expected & 0xFFFF)
            rows.append((case_id, packed))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as f:
        for _, packed in rows:
            f.write(f"{packed:015x}\n")

    print(f"Wrote {len(rows)} FDPE vectors to {args.out}")


if __name__ == "__main__":
    main()
