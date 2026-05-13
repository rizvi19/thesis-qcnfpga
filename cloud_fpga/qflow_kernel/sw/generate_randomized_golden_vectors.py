#!/usr/bin/env python3
"""
Generate fixed-seed randomized golden vectors for QFlow cloud-FPGA kernel.

This is Hardcore Local Check Step 2. It keeps the deterministic Step-1
vectors, then appends many fixed-seed randomized cases so the RTL selector,
invalid-path handling, no-path status, bottleneck-fidelity computation, and
score arithmetic are exercised before AWS EC2 F2 time is used.

Output:
  vectors/exp_lut.hex
  vectors/golden_vectors.csv

This script intentionally uses the same helper functions and scoring model as
sw/generate_golden_vectors.py to avoid changing the implementation contract.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SW_DIR = ROOT / "sw"
if str(SW_DIR) not in sys.path:
    sys.path.insert(0, str(SW_DIR))

import generate_golden_vectors as base  # noqa: E402

RANDOM_SEED = 20260514
N_RANDOM = 200
VEC_DIR = ROOT / "vectors"
VEC_DIR.mkdir(parents=True, exist_ok=True)

FIELDNAMES = [
    "test_id", "src_node", "dst_node", "time_now", "f_min_q016",
    "key_counts", "f_init_q016", "decay_idx", "arrival_rate_q8_8", "qber_q016", "distance_cost_q16_16",
    "candidate_paths", "candidate_lens", "expected_selected_path_id", "expected_best_weight",
    "expected_bottleneck_fidelity", "expected_valid_path", "tolerance", "intent",
]


def rand_edge(rng: random.Random, mode: str) -> dict:
    """Create one randomized edge using the same packed fields as Step 1."""
    if mode == "valid_biased":
        key_count = rng.choice([1, 2, 3, 4, 5, 6, 8, 10, 12, 15])
        f_init = rng.uniform(0.90, 0.995)
        decay_idx = rng.choice([0, 1, 2, 3, 4, 5, 8, 12])
        arrival = rng.choice([300, 511, 512, 700, 1023, 1024, 1200, 1500, 1800])
        qber = rng.choice([0.005, 0.01, 0.02, 0.03, 0.05, 0.08])
        km = rng.uniform(5, 35)
    elif mode == "invalid_biased":
        key_count = rng.choice([0, 0, 0, 1, 2, 3])
        f_init = rng.uniform(0.50, 0.93)
        decay_idx = rng.choice([0, 2, 8, 16, 32, 64, 128, 255])
        arrival = rng.choice([0, 100, 300, 511, 512, 900, 1200])
        qber = rng.choice([0.01, 0.05, 0.10, 0.15])
        km = rng.uniform(5, 50)
    else:  # mixed
        key_count = rng.choice([0, 1, 2, 3, 4, 7, 8, 15])
        f_init = rng.uniform(0.65, 0.995)
        decay_idx = rng.choice([0, 1, 2, 3, 8, 16, 32, 64, 128, 255])
        arrival = rng.choice([0, 128, 300, 511, 512, 700, 1023, 1024, 1600])
        qber = rng.choice([0.005, 0.01, 0.02, 0.05, 0.10, 0.15])
        km = rng.uniform(1, 60)
    return base.E(key_count, f_init, decay_idx, arrival, qber, km)


def make_candidate(rng: random.Random, invalid_edge_prob: float, zero_len_prob: float) -> tuple[list[int], int]:
    """Create one candidate path with occasional invalid/zero-length cases."""
    if rng.random() < zero_len_prob:
        return base.C(0), 0
    length = rng.choice([1, 1, 2, 2, 3, 4])
    ids: list[int] = []
    for _ in range(length):
        if rng.random() < invalid_edge_prob:
            ids.append(rng.choice([8, 9, 10, 15]))
        else:
            ids.append(rng.randrange(base.NUM_EDGES))
    return base.C(*ids), length


def random_vector(rng: random.Random, idx: int) -> dict:
    """Create a randomized vector definition in the same structure as Step 1."""
    # Cycle through scenario families so coverage is not purely accidental.
    family = idx % 5
    if family == 0:
        mode = "valid_biased"
        invalid_edge_prob = 0.02
        zero_len_prob = 0.00
        f_min = rng.uniform(0.70, 0.88)
        note = "random valid-biased regression"
    elif family == 1:
        mode = "mixed"
        invalid_edge_prob = 0.10
        zero_len_prob = 0.05
        f_min = rng.uniform(0.75, 0.92)
        note = "random mixed valid/invalid regression"
    elif family == 2:
        mode = "invalid_biased"
        invalid_edge_prob = 0.15
        zero_len_prob = 0.10
        f_min = rng.uniform(0.86, 0.97)
        note = "random invalid/no-path stress regression"
    elif family == 3:
        mode = "mixed"
        invalid_edge_prob = 0.05
        zero_len_prob = 0.00
        f_min = rng.uniform(0.90, 0.97)
        note = "random high-threshold regression"
    else:
        mode = "valid_biased"
        invalid_edge_prob = 0.00
        zero_len_prob = 0.00
        f_min = rng.uniform(0.65, 0.82)
        note = "random low-threshold arithmetic regression"

    edges = [rand_edge(rng, mode) for _ in range(base.NUM_EDGES)]
    candidates = []
    lens = []
    for _ in range(base.NUM_CAND):
        c, ln = make_candidate(rng, invalid_edge_prob, zero_len_prob)
        candidates.append(c)
        lens.append(ln)

    return {
        "test_id": f"R{idx:03d}_seeded_random",
        "src_node": rng.randrange(0, 8),
        "dst_node": rng.randrange(0, 8),
        "time_now": 2000 + idx,
        "f_min_q016": base.q016(f_min),
        "edges": base.pad_edges(edges),
        "candidates": candidates,
        "candidate_lens": lens,
        "expect_id": None,
        "note": note,
    }


def write_vectors(vector_defs: list[dict]) -> None:
    lut = base.make_exp_lut()
    base.write_hex_lut(lut)

    with (VEC_DIR / "golden_vectors.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for v in vector_defs:
            best_id, best_score, best_bottleneck, valid, rows = base.select_path(
                v["candidates"], v["candidate_lens"], v["edges"], v["f_min_q016"], lut
            )
            writer.writerow({
                "test_id": v["test_id"],
                "src_node": v["src_node"],
                "dst_node": v["dst_node"],
                "time_now": v["time_now"],
                "f_min_q016": v["f_min_q016"],
                "key_counts": base.flatten_edges(v["edges"], "key_count"),
                "f_init_q016": base.flatten_edges(v["edges"], "f_init_q016"),
                "decay_idx": base.flatten_edges(v["edges"], "decay_idx"),
                "arrival_rate_q8_8": base.flatten_edges(v["edges"], "arrival_rate_q8_8"),
                "qber_q016": base.flatten_edges(v["edges"], "qber_q016"),
                "distance_cost_q16_16": base.flatten_edges(v["edges"], "distance_cost_q16_16"),
                "candidate_paths": base.flatten_candidates(v["candidates"]),
                "candidate_lens": "|".join(str(x) for x in v["candidate_lens"]),
                "expected_selected_path_id": best_id,
                "expected_best_weight": best_score,
                "expected_bottleneck_fidelity": best_bottleneck,
                "expected_valid_path": valid,
                "tolerance": 0,
                "intent": v.get("note", ""),
            })


def main() -> None:
    rng = random.Random(RANDOM_SEED)
    deterministic = base.build_vectors()
    randomized = [random_vector(rng, idx) for idx in range(N_RANDOM)]
    vectors = deterministic + randomized
    write_vectors(vectors)
    print(f"Wrote {VEC_DIR / 'exp_lut.hex'}")
    print(f"Wrote {VEC_DIR / 'golden_vectors.csv'}")
    print(f"Deterministic vectors: {len(deterministic)}")
    print(f"Randomized vectors: {len(randomized)}")
    print(f"Total vector count: {len(vectors)}")
    print(f"Random seed: {RANDOM_SEED}")


if __name__ == "__main__":
    main()
