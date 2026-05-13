#!/usr/bin/env python3
"""Compare QFlow cloud-kernel hardware output against golden vectors."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def read_csv(path: Path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default="vectors/golden_vectors.csv")
    ap.add_argument("--hw", default="results/hardware_output.csv")
    ap.add_argument("--out", default="results/hardware_vs_python.csv")
    args = ap.parse_args()

    golden_rows = {r["test_id"].strip(): r for r in read_csv(Path(args.golden))}
    hw_rows = read_csv(Path(args.hw))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    failures = 0
    total = 0

    with out_path.open("w", newline="") as f:
        fieldnames = [
            "test_id", "selected_match", "weight_abs_error", "fidelity_abs_error",
            "latency_cycles", "pass_fail", "details",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for hw in hw_rows:
            total += 1
            test_id = hw["test_id"].strip()
            g = golden_rows.get(test_id)
            if g is None:
                failures += 1
                writer.writerow({
                    "test_id": test_id,
                    "selected_match": 0,
                    "weight_abs_error": "NA",
                    "fidelity_abs_error": "NA",
                    "latency_cycles": hw.get("latency_cycles", ""),
                    "pass_fail": "FAIL",
                    "details": "missing golden row",
                })
                continue

            tol = int(g.get("tolerance", 0) or 0)
            selected_match = int(int(hw["selected_path_id"]) == int(g["expected_selected_path_id"]))
            weight_err = abs(int(hw["best_weight"]) - int(g["expected_best_weight"]))
            fid_err = abs(int(hw["bottleneck_fidelity"]) - int(g["expected_bottleneck_fidelity"]))
            ok = selected_match and weight_err <= tol and fid_err <= tol
            if not ok:
                failures += 1
            writer.writerow({
                "test_id": test_id,
                "selected_match": selected_match,
                "weight_abs_error": weight_err,
                "fidelity_abs_error": fid_err,
                "latency_cycles": hw.get("latency_cycles", ""),
                "pass_fail": "PASS" if ok else "FAIL",
                "details": "" if ok else "mismatch outside tolerance",
            })

    print(f"Compared {total} row(s). PASS={total-failures}, FAIL={failures}. Output: {out_path}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
