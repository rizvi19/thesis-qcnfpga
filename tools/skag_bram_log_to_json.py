#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def parse_hex(value: str) -> int:
    value = value.strip()
    if value.lower().startswith('0x'):
        value = value[2:]
    if any(ch in value.lower() for ch in 'xz'):
        return 0
    return int(value, 16)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert SKAG BRAM sim CSV log to summary JSON.")
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    vector_count = 0
    pass_count = 0
    fail_count = 0
    first_fail = None
    max_weight_diff = 0

    with args.csv.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            vector_count += 1
            passed = int(row["pass"])
            exp_valid = int(row.get("exp_ga_valid", "0"))
            obs_valid = int(row.get("obs_ga_valid", "0"))
            if exp_valid and obs_valid:
                exp_w = parse_hex(row["exp_ga_weight"])
                obs_w = parse_hex(row["obs_ga_weight"])
                diff = abs(obs_w - exp_w)
                if diff > max_weight_diff:
                    max_weight_diff = diff
            if passed:
                pass_count += 1
            else:
                fail_count += 1
                if first_fail is None:
                    first_fail = {
                        "cycle": int(row["cycle"]),
                        "exp_ga_valid": exp_valid,
                        "obs_ga_valid": obs_valid,
                        "exp_ga_edge": row["exp_ga_edge"],
                        "obs_ga_edge": row["obs_ga_edge"],
                        "exp_ga_weight": row["exp_ga_weight"],
                        "obs_ga_weight": row["obs_ga_weight"],
                    }

    payload = {
        "vector_count": vector_count,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "max_weight_diff": max_weight_diff,
        "first_fail": first_fail,
        "overall_pass": fail_count == 0,
    }
    args.out.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
