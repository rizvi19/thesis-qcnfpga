#!/usr/bin/env python3
"""
Generate deterministic golden vectors for the first QFlow AWS F2 cloud-FPGA kernel.

The goal of this file is not to replace the full QFlow reference model. It produces a small,
fixed, host-to-FPGA validation vector set for the cloud kernel:
  FDPE-style fidelity update -> SKAG-style edge score -> candidate path selector.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

FID_SCALE = 65535
NUM_EDGES = 8
NUM_CAND = 4
MAX_PATH_EDGES = 4
INF_SCORE = 0xFFFFFFFF

ROOT = Path(__file__).resolve().parents[1]
VEC_DIR = ROOT / "vectors"
VEC_DIR.mkdir(parents=True, exist_ok=True)


def q016(x: float) -> int:
    return max(0, min(FID_SCALE, int(round(x * FID_SCALE))))


def km_cost(km: float) -> int:
    # Q16.16-like integer cost; distance is only a component of the rank score.
    return int(round(km * 65536.0))


def make_exp_lut() -> list[int]:
    return [q016(math.exp(-(i / 32.0))) for i in range(256)]


def fdpe_fidelity(f_init_q016: int, decay_idx: int, lut: list[int]) -> int:
    decay_idx = max(0, min(255, decay_idx))
    return (f_init_q016 * lut[decay_idx]) >> 16


def edge_score(edge: dict, f_min: int, lut: list[int]) -> tuple[int, int, int]:
    key_count = int(edge["key_count"])
    fid = fdpe_fidelity(int(edge["f_init_q016"]), int(edge["decay_idx"]), lut)
    arrival = int(edge["arrival_rate_q8_8"])
    qber = int(edge["qber_q016"])
    dist = int(edge["distance_cost_q16_16"])

    valid = int(key_count > 0 and fid >= f_min)
    if not valid:
        return INF_SCORE, fid, 0

    # Hardware-friendly bucketed penalties. This avoids divider-heavy RTL for the first F2 run.
    if key_count < 2:
        scarcity = 32768
    elif key_count < 4:
        scarcity = 16384
    elif key_count < 8:
        scarcity = 8192
    else:
        scarcity = 4096

    if arrival < 512:
        arrival_penalty = 32768
    elif arrival < 1024:
        arrival_penalty = 16384
    else:
        arrival_penalty = 8192

    fidelity_penalty = (FID_SCALE - fid) << 3
    qber_penalty = qber << 1
    score = dist + scarcity + arrival_penalty + fidelity_penalty + qber_penalty
    return score, fid, valid


def path_score(cand: list[int], length: int, edges: list[dict], f_min: int, lut: list[int]) -> tuple[int, int, int]:
    total = 0
    bottleneck = FID_SCALE
    valid_path = 1 if length > 0 else 0
    for idx in cand[:length]:
        s, fid, valid = edge_score(edges[idx], f_min, lut)
        if not valid:
            valid_path = 0
        if s >= INF_SCORE:
            total = INF_SCORE
        elif total < INF_SCORE:
            total += s
            if total > INF_SCORE:
                total = INF_SCORE
        bottleneck = min(bottleneck, fid)
    return total, bottleneck, valid_path


def select_path(candidates: list[list[int]], cand_lens: list[int], edges: list[dict], f_min: int, lut: list[int]):
    best_id = 0
    best_score = INF_SCORE
    best_bottleneck = 0
    any_valid = 0
    rows = []
    for cid, cand in enumerate(candidates):
        score, bottleneck, valid = path_score(cand, cand_lens[cid], edges, f_min, lut)
        rows.append((cid, score, bottleneck, valid))
        if valid and score < best_score:
            best_id = cid
            best_score = score
            best_bottleneck = bottleneck
            any_valid = 1
    if not any_valid:
        return 0, INF_SCORE, 0, 0, rows
    return best_id, best_score, best_bottleneck, 1, rows


def write_hex_lut(lut: list[int]) -> None:
    with (VEC_DIR / "exp_lut.hex").open("w") as f:
        for value in lut:
            f.write(f"{value:04x}\n")


def flatten_edges(edges: list[dict], field: str) -> str:
    return "|".join(str(int(e[field])) for e in edges)


def flatten_candidates(cands: list[list[int]]) -> str:
    return "|".join("-".join(str(x) for x in cand) for cand in cands)


def main() -> None:
    lut = make_exp_lut()
    write_hex_lut(lut)

    # Three deterministic vectors. They intentionally exercise:
    # 1) normal best-path selection,
    # 2) blocked edge rejection,
    # 3) high threshold causing a different valid candidate.
    vector_defs = [
        {
            "test_id": "T001_normal_ring6",
            "src_node": 0,
            "dst_node": 3,
            "time_now": 1000,
            "f_min_q016": q016(0.85),
            "edges": [
                {"key_count": 6,  "f_init_q016": q016(0.97), "decay_idx": 1, "arrival_rate_q8_8": 1200, "qber_q016": q016(0.02), "distance_cost_q16_16": km_cost(20)},
                {"key_count": 5,  "f_init_q016": q016(0.96), "decay_idx": 1, "arrival_rate_q8_8": 1150, "qber_q016": q016(0.03), "distance_cost_q16_16": km_cost(22)},
                {"key_count": 4,  "f_init_q016": q016(0.98), "decay_idx": 2, "arrival_rate_q8_8": 1000, "qber_q016": q016(0.02), "distance_cost_q16_16": km_cost(19)},
                {"key_count": 9,  "f_init_q016": q016(0.99), "decay_idx": 1, "arrival_rate_q8_8": 1400, "qber_q016": q016(0.01), "distance_cost_q16_16": km_cost(18)},
                {"key_count": 8,  "f_init_q016": q016(0.98), "decay_idx": 1, "arrival_rate_q8_8": 1300, "qber_q016": q016(0.02), "distance_cost_q16_16": km_cost(18)},
                {"key_count": 7,  "f_init_q016": q016(0.97), "decay_idx": 1, "arrival_rate_q8_8": 1250, "qber_q016": q016(0.02), "distance_cost_q16_16": km_cost(18)},
                {"key_count": 3,  "f_init_q016": q016(0.99), "decay_idx": 3, "arrival_rate_q8_8": 700,  "qber_q016": q016(0.01), "distance_cost_q16_16": km_cost(25)},
                {"key_count": 0,  "f_init_q016": q016(0.99), "decay_idx": 0, "arrival_rate_q8_8": 900,  "qber_q016": q016(0.01), "distance_cost_q16_16": km_cost(10)},
            ],
            "candidates": [[0, 1, 2, 0], [3, 4, 5, 0], [0, 6, 5, 0], [7, 0, 0, 0]],
            "candidate_lens": [3, 3, 3, 1],
        },
        {
            "test_id": "T002_blocked_candidate",
            "src_node": 0,
            "dst_node": 3,
            "time_now": 2000,
            "f_min_q016": q016(0.86),
            "edges": [
                {"key_count": 2,  "f_init_q016": q016(0.95), "decay_idx": 2, "arrival_rate_q8_8": 850,  "qber_q016": q016(0.03), "distance_cost_q16_16": km_cost(21)},
                {"key_count": 0,  "f_init_q016": q016(0.95), "decay_idx": 2, "arrival_rate_q8_8": 850,  "qber_q016": q016(0.03), "distance_cost_q16_16": km_cost(21)},
                {"key_count": 4,  "f_init_q016": q016(0.98), "decay_idx": 1, "arrival_rate_q8_8": 1100, "qber_q016": q016(0.02), "distance_cost_q16_16": km_cost(22)},
                {"key_count": 7,  "f_init_q016": q016(0.99), "decay_idx": 1, "arrival_rate_q8_8": 1200, "qber_q016": q016(0.01), "distance_cost_q16_16": km_cost(23)},
                {"key_count": 8,  "f_init_q016": q016(0.98), "decay_idx": 1, "arrival_rate_q8_8": 1250, "qber_q016": q016(0.02), "distance_cost_q16_16": km_cost(23)},
                {"key_count": 8,  "f_init_q016": q016(0.97), "decay_idx": 1, "arrival_rate_q8_8": 1250, "qber_q016": q016(0.02), "distance_cost_q16_16": km_cost(23)},
                {"key_count": 6,  "f_init_q016": q016(0.96), "decay_idx": 4, "arrival_rate_q8_8": 600,  "qber_q016": q016(0.03), "distance_cost_q16_16": km_cost(20)},
                {"key_count": 3,  "f_init_q016": q016(0.99), "decay_idx": 0, "arrival_rate_q8_8": 1300, "qber_q016": q016(0.01), "distance_cost_q16_16": km_cost(30)},
            ],
            "candidates": [[0, 1, 2, 0], [3, 4, 5, 0], [0, 6, 5, 0], [7, 0, 0, 0]],
            "candidate_lens": [3, 3, 3, 1],
        },
        {
            "test_id": "T003_high_threshold",
            "src_node": 0,
            "dst_node": 3,
            "time_now": 3000,
            "f_min_q016": q016(0.93),
            "edges": [
                {"key_count": 6,  "f_init_q016": q016(0.97), "decay_idx": 3, "arrival_rate_q8_8": 1200, "qber_q016": q016(0.02), "distance_cost_q16_16": km_cost(20)},
                {"key_count": 5,  "f_init_q016": q016(0.96), "decay_idx": 4, "arrival_rate_q8_8": 1150, "qber_q016": q016(0.03), "distance_cost_q16_16": km_cost(22)},
                {"key_count": 4,  "f_init_q016": q016(0.98), "decay_idx": 4, "arrival_rate_q8_8": 1000, "qber_q016": q016(0.02), "distance_cost_q16_16": km_cost(19)},
                {"key_count": 9,  "f_init_q016": q016(0.99), "decay_idx": 0, "arrival_rate_q8_8": 1400, "qber_q016": q016(0.01), "distance_cost_q16_16": km_cost(18)},
                {"key_count": 8,  "f_init_q016": q016(0.98), "decay_idx": 0, "arrival_rate_q8_8": 1300, "qber_q016": q016(0.02), "distance_cost_q16_16": km_cost(18)},
                {"key_count": 7,  "f_init_q016": q016(0.97), "decay_idx": 0, "arrival_rate_q8_8": 1250, "qber_q016": q016(0.02), "distance_cost_q16_16": km_cost(18)},
                {"key_count": 3,  "f_init_q016": q016(0.99), "decay_idx": 5, "arrival_rate_q8_8": 700,  "qber_q016": q016(0.01), "distance_cost_q16_16": km_cost(25)},
                {"key_count": 0,  "f_init_q016": q016(0.99), "decay_idx": 0, "arrival_rate_q8_8": 900,  "qber_q016": q016(0.01), "distance_cost_q16_16": km_cost(10)},
            ],
            "candidates": [[0, 1, 2, 0], [3, 4, 5, 0], [0, 6, 5, 0], [7, 0, 0, 0]],
            "candidate_lens": [3, 3, 3, 1],
        },
    ]

    fieldnames = [
        "test_id", "src_node", "dst_node", "time_now", "f_min_q016",
        "key_counts", "f_init_q016", "decay_idx", "arrival_rate_q8_8", "qber_q016", "distance_cost_q16_16",
        "candidate_paths", "candidate_lens", "expected_selected_path_id", "expected_best_weight",
        "expected_bottleneck_fidelity", "expected_valid_path", "tolerance",
    ]

    with (VEC_DIR / "golden_vectors.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for v in vector_defs:
            best_id, best_score, best_bottleneck, valid, _rows = select_path(
                v["candidates"], v["candidate_lens"], v["edges"], v["f_min_q016"], lut
            )
            writer.writerow({
                "test_id": v["test_id"],
                "src_node": v["src_node"],
                "dst_node": v["dst_node"],
                "time_now": v["time_now"],
                "f_min_q016": v["f_min_q016"],
                "key_counts": flatten_edges(v["edges"], "key_count"),
                "f_init_q016": flatten_edges(v["edges"], "f_init_q016"),
                "decay_idx": flatten_edges(v["edges"], "decay_idx"),
                "arrival_rate_q8_8": flatten_edges(v["edges"], "arrival_rate_q8_8"),
                "qber_q016": flatten_edges(v["edges"], "qber_q016"),
                "distance_cost_q16_16": flatten_edges(v["edges"], "distance_cost_q16_16"),
                "candidate_paths": flatten_candidates(v["candidates"]),
                "candidate_lens": "|".join(str(x) for x in v["candidate_lens"]),
                "expected_selected_path_id": best_id,
                "expected_best_weight": best_score,
                "expected_bottleneck_fidelity": best_bottleneck,
                "expected_valid_path": valid,
                "tolerance": 0,
            })
    print(f"Wrote {VEC_DIR / 'exp_lut.hex'}")
    print(f"Wrote {VEC_DIR / 'golden_vectors.csv'}")


if __name__ == "__main__":
    main()
