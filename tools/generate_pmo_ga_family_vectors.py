#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from pathlib import Path

CANDIDATES = [
    {"id": 0, "latency_q16_16": 0x00064000, "fidelity_q0_16": 59000, "util_q0_16": 15000, "gene16": 0x1234},
    {"id": 1, "latency_q16_16": 0x00062000, "fidelity_q0_16": 58000, "util_q0_16": 14900, "gene16": 0x5678},
    {"id": 2, "latency_q16_16": 0x00058000, "fidelity_q0_16": 60000, "util_q0_16": 15200, "gene16": 0x89AB},
    {"id": 3, "latency_q16_16": 0x00054000, "fidelity_q0_16": 60500, "util_q0_16": 14800, "gene16": 0xCDEF},
    {"id": 4, "latency_q16_16": 0x00050000, "fidelity_q0_16": 60948, "util_q0_16": 14418, "gene16": 0xACE1},
    {"id": 5, "latency_q16_16": 0x00052000, "fidelity_q0_16": 60700, "util_q0_16": 14500, "gene16": 0x0F0F},
    {"id": 6, "latency_q16_16": 0x00060000, "fidelity_q0_16": 59500, "util_q0_16": 14600, "gene16": 0x3333},
    {"id": 7, "latency_q16_16": 0x00070000, "fidelity_q0_16": 61000, "util_q0_16": 16000, "gene16": 0xAAAA},
]

EXPECTED = {
    "vector_count": len(CANDIDATES),
    "expected_best_id": 4,
    "expected_best_path": [0, 5, 4, 3],
    "expected_latency_q16_16": 0x00050000,
    "expected_fidelity_q0_16": 60948,
    "expected_util_q0_16": 14418,
    "expected_child_gene16": 0x1278,
    "expected_mutated_gene16": 0x127C,
    "notes": [
        "Step 6B exercises the PMO-GA family wiring with request/stream control.",
        "This is still a smoke-integration milestone before a full multi-generation engine."
    ]
}

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out-dir', default='results/phase5')
    ap.add_argument('--tb-dir', default='tb')
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    tb_dir = Path(args.tb_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tb_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / 'pmo_ga_family_candidates.csv'
    memh_path = tb_dir / 'pmo_ga_family_vectors.memh'
    expected_path = out_dir / 'pmo_ga_family_expected.json'

    with csv_path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['id', 'latency_q16_16', 'fidelity_q0_16', 'util_q0_16', 'gene16'])
        w.writeheader()
        for row in CANDIDATES:
            w.writerow(row)

    with memh_path.open('w') as f:
        for row in CANDIDATES:
            packed = ((row['gene16'] & 0xFFFF) << 80) | ((row['id'] & 0xFFFF) << 64) | ((row['latency_q16_16'] & 0xFFFFFFFF) << 32) | ((row['fidelity_q0_16'] & 0xFFFF) << 16) | (row['util_q0_16'] & 0xFFFF)
            f.write(f"{packed:024x}\n")

    expected_path.write_text(json.dumps(EXPECTED, indent=2))
    print(f"Wrote {len(CANDIDATES)} PMO-GA family candidates to {memh_path}")
    print(f" - {csv_path}")
    print(f" - {expected_path}")

if __name__ == '__main__':
    main()
