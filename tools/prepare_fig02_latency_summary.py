#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_kv_file(path: Path):
    data = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hw-summary", default="results/phase10_latency/qflow_top_tc5_latency_summary.txt")
    ap.add_argument("--sw-csv", default="results/phase10_latency/sw_latency_benchmark.csv")
    ap.add_argument("--out", default="results/paper/data/figures/fig02_latency/source/latency_summary.csv")
    args = ap.parse_args()

    hw = parse_kv_file(Path(args.hw_summary))

    # Use GA selection latency for the main plot.
    # This is the fairest comparison against software routing decision runtimes.
    hw_ga_ns = float(hw["ga_latency_ns"])
    hw_ga_us = hw_ga_ns / 1000.0

    rows = [
        {
            "method_id": "qflow_hw",
            "display_name": "QFlow hardware",
            "domain": "hardware",
            "latency_value": f"{hw_ga_us:.6f}",
            "latency_unit": "us",
            "quantity_type": "derived_from_cycle_count_at_100MHz",
            "source_basis": "ga_selection_cycles_from_ga_start_to_ga_result_valid",
            "include_in_main_plot": "yes",
            "notes": "Main FIG02 hardware bar uses GA selection path only"
        }
    ]

    with open(args.sw_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "method_id": r["method_id"],
                "display_name": r["display_name"],
                "domain": r["domain"],
                "latency_value": f"{float(r['median_us']):.6f}",
                "latency_unit": "us",
                "quantity_type": r["quantity_type"],
                "source_basis": f"median_of_{r['iterations']}_runs",
                "include_in_main_plot": "yes",
                "notes": ""
            })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "method_id", "display_name", "domain", "latency_value",
                "latency_unit", "quantity_type", "source_basis",
                "include_in_main_plot", "notes"
            ]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
