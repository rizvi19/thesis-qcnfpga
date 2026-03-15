#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarise FDPE simulation CSV log into JSON.")
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    rows = list(csv.DictReader(args.csv.open()))
    vector_count = len(rows)
    fail_rows = [r for r in rows if r["pass"] != "1"]
    max_abs_diff = max((int(r["abs_diff_lsb"]) for r in rows), default=0)

    summary = {
        "vector_count": vector_count,
        "fail_count": len(fail_rows),
        "pass_count": vector_count - len(fail_rows),
        "max_abs_diff_lsb": max_abs_diff,
        "first_fail": fail_rows[0] if fail_rows else None,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
