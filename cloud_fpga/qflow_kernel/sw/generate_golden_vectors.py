#!/usr/bin/env python3
"""
Generate extended deterministic golden vectors for the QFlow AWS F2 cloud-FPGA kernel.

This is the Step-1 local hardening suite. It keeps the first AWS target small:
FDPE-style fidelity update -> SKAG-style edge rank score -> candidate path selector.

The vectors intentionally cover normal selection, blocked edges, no-valid-path,
tie-breaking, key scarcity, fidelity threshold, QBER penalty, arrival-rate penalty,
distance penalty, invalid edge IDs, zero-length candidates, decay boundaries, and
start/done repeatability through multiple generated transactions.
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
    return int(round(km * 65536.0))


def make_exp_lut() -> list[int]:
    # Must match fdpe_kernel.v: LUT[i] = round(exp(-(i/32))*65535)
    return [q016(math.exp(-(i / 32.0))) for i in range(256)]


def fdpe_fidelity(f_init_q016: int, decay_idx: int, lut: list[int]) -> int:
    decay_idx = max(0, min(255, decay_idx))
    return (int(f_init_q016) * int(lut[decay_idx])) >> 16


def edge_score(edge: dict, f_min: int, lut: list[int]) -> tuple[int, int, int]:
    key_count = int(edge["key_count"])
    fid = fdpe_fidelity(int(edge["f_init_q016"]), int(edge["decay_idx"]), lut)
    arrival = int(edge["arrival_rate_q8_8"])
    qber = int(edge["qber_q016"])
    dist = int(edge["distance_cost_q16_16"])

    valid = int(key_count > 0 and fid >= f_min)
    if not valid:
        return INF_SCORE, fid, 0

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
    return score & 0xFFFFFFFF, fid, valid


def path_score(cand: list[int], length: int, edges: list[dict], f_min: int, lut: list[int]) -> tuple[int, int, int]:
    total = 0
    bottleneck = FID_SCALE
    valid_path = 1 if length > 0 else 0

    for idx in cand[:length]:
        if idx < 0 or idx >= NUM_EDGES:
            valid_path = 0
            continue
        s, fid, valid = edge_score(edges[idx], f_min, lut)
        if not valid:
            valid_path = 0
        if s >= INF_SCORE:
            # Keep the value consistent with the RTL path-selection contract for invalid edges:
            # invalid paths will never be selected, so exact invalid total is not selected.
            total = INF_SCORE
        elif total < INF_SCORE:
            total = (total + s) & 0xFFFFFFFF
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
        # RTL uses strict <, so equal-score ties preserve the earlier candidate.
        if valid and score < best_score:
            best_id = cid
            best_score = score
            best_bottleneck = bottleneck
            any_valid = 1
    if not any_valid:
        return 0, INF_SCORE, 0, 0, rows
    return best_id, best_score, best_bottleneck, 1, rows


def E(key_count: int, f_init: float, decay_idx: int, arrival: int, qber: float, km: float) -> dict:
    return {
        "key_count": key_count,
        "f_init_q016": q016(f_init),
        "decay_idx": decay_idx,
        "arrival_rate_q8_8": arrival,
        "qber_q016": q016(qber),
        "distance_cost_q16_16": km_cost(km),
    }


def pad_edges(edges: list[dict]) -> list[dict]:
    filler = E(0, 0.90, 0, 0, 0.10, 99)
    out = list(edges)
    while len(out) < NUM_EDGES:
        out.append(filler.copy())
    return out[:NUM_EDGES]


def C(*edge_ids: int) -> list[int]:
    out = list(edge_ids)
    while len(out) < MAX_PATH_EDGES:
        out.append(0)
    return out[:MAX_PATH_EDGES]


def vec(test_id: str, src: int, dst: int, f_min: float, edges: list[dict], candidates: list[list[int]], lens: list[int], expect_id: int | None = None, note: str = "") -> dict:
    assert len(candidates) == NUM_CAND, f"{test_id}: need {NUM_CAND} candidates"
    assert len(lens) == NUM_CAND, f"{test_id}: need {NUM_CAND} lengths"
    return {
        "test_id": test_id,
        "src_node": src,
        "dst_node": dst,
        "time_now": 1000 + len(test_id) * 17,
        "f_min_q016": q016(f_min),
        "edges": pad_edges(edges),
        "candidates": candidates,
        "candidate_lens": lens,
        "expect_id": expect_id,
        "note": note,
    }


def flatten_edges(edges: list[dict], field: str) -> str:
    return "|".join(str(int(e[field])) for e in edges)


def flatten_candidates(cands: list[list[int]]) -> str:
    return "|".join("-".join(str(x) for x in cand) for cand in cands)


def write_hex_lut(lut: list[int]) -> None:
    with (VEC_DIR / "exp_lut.hex").open("w") as f:
        for value in lut:
            f.write(f"{value:04x}\n")


def build_vectors() -> list[dict]:
    vectors: list[dict] = []

    # T001-T003 preserve the first passing smoke checks.
    vectors.append(vec(
        "T001_normal_ring6", 0, 3, 0.85,
        [
            E(6, 0.97, 1, 1200, 0.02, 20), E(5, 0.96, 1, 1150, 0.03, 22), E(4, 0.98, 2, 1000, 0.02, 19),
            E(9, 0.99, 1, 1400, 0.01, 18), E(8, 0.98, 1, 1300, 0.02, 18), E(7, 0.97, 1, 1250, 0.02, 18),
            E(3, 0.99, 3, 700, 0.01, 25), E(0, 0.99, 0, 900, 0.01, 10),
        ],
        [C(0, 1, 2), C(3, 4, 5), C(0, 6, 5), C(7)], [3, 3, 3, 1], 1,
        "normal best-path selection"
    ))

    vectors.append(vec(
        "T002_blocked_candidate", 0, 3, 0.86,
        [
            E(2, 0.95, 2, 850, 0.03, 21), E(0, 0.95, 2, 850, 0.03, 21), E(4, 0.98, 1, 1100, 0.02, 22),
            E(7, 0.99, 1, 1200, 0.01, 23), E(8, 0.98, 1, 1250, 0.02, 23), E(8, 0.97, 1, 1250, 0.02, 23),
            E(6, 0.96, 4, 600, 0.03, 20), E(3, 0.99, 0, 1300, 0.01, 30),
        ],
        [C(0, 1, 2), C(3, 4, 5), C(0, 6, 5), C(7)], [3, 3, 3, 1], 3,
        "blocked edge rejection"
    ))

    vectors.append(vec(
        "T003_high_threshold", 0, 3, 0.93,
        [
            E(6, 0.97, 3, 1200, 0.02, 20), E(5, 0.96, 4, 1150, 0.03, 22), E(4, 0.98, 4, 1000, 0.02, 19),
            E(9, 0.99, 0, 1400, 0.01, 18), E(8, 0.98, 0, 1300, 0.02, 18), E(7, 0.97, 0, 1250, 0.02, 18),
            E(3, 0.99, 5, 700, 0.01, 25), E(0, 0.99, 0, 900, 0.01, 10),
        ],
        [C(0, 1, 2), C(3, 4, 5), C(0, 6, 5), C(7)], [3, 3, 3, 1], 1,
        "threshold moves selection away from decayed path"
    ))

    # New deterministic hardening vectors.
    vectors.append(vec(
        "T004_all_candidates_valid", 0, 5, 0.80,
        [E(8, 0.98, 0, 1500, 0.01, 15), E(8, 0.98, 0, 1500, 0.01, 16),
         E(8, 0.99, 0, 1500, 0.01, 10), E(8, 0.99, 0, 1500, 0.01, 10),
         E(4, 0.96, 1, 1100, 0.02, 12), E(4, 0.96, 1, 1100, 0.02, 12),
         E(2, 0.95, 2, 900, 0.03, 13), E(2, 0.95, 2, 900, 0.03, 13)],
        [C(0, 1), C(2, 3), C(4, 5), C(6, 7)], [2, 2, 2, 2], 1,
        "all candidates valid; lower score wins"
    ))

    vectors.append(vec(
        "T005_no_valid_path", 0, 5, 0.95,
        [E(0, 0.99, 0, 1500, 0.01, 10), E(1, 0.80, 0, 1500, 0.01, 10), E(2, 0.90, 8, 1500, 0.01, 10), E(0, 0.99, 0, 1500, 0.01, 10),
         E(0, 0.99, 0, 1500, 0.01, 10), E(1, 0.84, 1, 1500, 0.01, 10), E(1, 0.70, 0, 1500, 0.01, 10), E(0, 0.99, 0, 1500, 0.01, 10)],
        [C(0), C(1), C(2), C(5)], [1, 1, 1, 1], 0,
        "no candidate is valid; no_path should assert"
    ))

    vectors.append(vec(
        "T006_equal_weight_tie", 0, 5, 0.80,
        [E(8, 0.98, 0, 1200, 0.01, 10), E(8, 0.98, 0, 1200, 0.01, 10), E(8, 0.98, 0, 1200, 0.01, 14),
         E(8, 0.98, 0, 1200, 0.01, 14), E(8, 0.98, 0, 1200, 0.01, 20), E(8, 0.98, 0, 1200, 0.01, 20)],
        [C(0), C(1), C(2), C(3)], [1, 1, 1, 1], 0,
        "equal best score tie; earliest candidate must win"
    ))

    vectors.append(vec(
        "T007_low_key_penalty", 0, 5, 0.80,
        [E(1, 0.99, 0, 1500, 0.01, 10), E(8, 0.99, 0, 1500, 0.01, 10), E(3, 0.99, 0, 1500, 0.01, 10), E(6, 0.99, 0, 1500, 0.01, 10)],
        [C(0), C(1), C(2), C(3)], [1, 1, 1, 1], 1,
        "scarcity penalty should avoid key_count=1"
    ))

    vectors.append(vec(
        "T008_low_fidelity_penalty", 0, 5, 0.70,
        [E(8, 0.90, 0, 1500, 0.01, 10), E(8, 0.99, 0, 1500, 0.01, 10), E(8, 0.95, 0, 1500, 0.01, 10), E(8, 0.97, 0, 1500, 0.01, 10)],
        [C(0), C(1), C(2), C(3)], [1, 1, 1, 1], 1,
        "higher fidelity should reduce penalty"
    ))

    vectors.append(vec(
        "T009_high_qber_penalty", 0, 5, 0.70,
        [E(8, 0.98, 0, 1500, 0.10, 10), E(8, 0.98, 0, 1500, 0.01, 10), E(8, 0.98, 0, 1500, 0.05, 10), E(8, 0.98, 0, 1500, 0.03, 10)],
        [C(0), C(1), C(2), C(3)], [1, 1, 1, 1], 1,
        "lower QBER should reduce penalty"
    ))

    vectors.append(vec(
        "T010_distance_penalty", 0, 5, 0.70,
        [E(8, 0.98, 0, 1500, 0.01, 30), E(8, 0.98, 0, 1500, 0.01, 10), E(8, 0.98, 0, 1500, 0.01, 20), E(8, 0.98, 0, 1500, 0.01, 25)],
        [C(0), C(1), C(2), C(3)], [1, 1, 1, 1], 1,
        "shorter distance/cost should win"
    ))

    vectors.append(vec(
        "T011_invalid_edge_id", 0, 5, 0.70,
        [E(8, 0.98, 0, 1500, 0.01, 10), E(8, 0.98, 0, 1500, 0.01, 11), E(8, 0.98, 0, 1500, 0.01, 12), E(8, 0.98, 0, 1500, 0.01, 13)],
        [C(9), C(1), C(2), C(3)], [1, 1, 1, 1], 1,
        "candidate with edge ID >= NUM_EDGES must be invalid"
    ))

    vectors.append(vec(
        "T012_zero_length_candidate", 0, 5, 0.70,
        [E(8, 0.98, 0, 1500, 0.01, 10), E(8, 0.98, 0, 1500, 0.01, 9), E(8, 0.98, 0, 1500, 0.01, 11), E(8, 0.98, 0, 1500, 0.01, 12)],
        [C(0), C(1), C(2), C(3)], [0, 1, 1, 1], 1,
        "zero-length candidate is invalid"
    ))

    vectors.append(vec(
        "T013_arrival_bucket_penalty", 0, 5, 0.70,
        [E(8, 0.98, 0, 300, 0.01, 10), E(8, 0.98, 0, 700, 0.01, 10), E(8, 0.98, 0, 1500, 0.01, 10), E(8, 0.98, 0, 1024, 0.01, 10)],
        [C(0), C(1), C(2), C(3)], [1, 1, 1, 1], 2,
        "high arrival-rate bucket should win; tie with edge3 resolved by earlier edge2"
    ))

    vectors.append(vec(
        "T014_decay_zero_boundary", 0, 5, 0.70,
        [E(8, 0.97, 0, 1500, 0.01, 10), E(8, 0.97, 1, 1500, 0.01, 10), E(8, 0.97, 2, 1500, 0.01, 10), E(8, 0.97, 3, 1500, 0.01, 10)],
        [C(0), C(1), C(2), C(3)], [1, 1, 1, 1], 0,
        "decay_idx=0 should preserve maximum fidelity"
    ))

    vectors.append(vec(
        "T015_decay_max_boundary", 0, 5, 0.50,
        [E(8, 0.99, 255, 1500, 0.01, 10), E(8, 0.99, 128, 1500, 0.01, 11), E(8, 0.99, 64, 1500, 0.01, 12), E(8, 0.99, 0, 1500, 0.01, 13)],
        [C(0), C(1), C(2), C(3)], [1, 1, 1, 1], 3,
        "maximum decay should be avoided under fidelity threshold"
    ))

    return vectors


def main() -> None:
    lut = make_exp_lut()
    write_hex_lut(lut)
    vector_defs = build_vectors()

    fieldnames = [
        "test_id", "src_node", "dst_node", "time_now", "f_min_q016",
        "key_counts", "f_init_q016", "decay_idx", "arrival_rate_q8_8", "qber_q016", "distance_cost_q16_16",
        "candidate_paths", "candidate_lens", "expected_selected_path_id", "expected_best_weight",
        "expected_bottleneck_fidelity", "expected_valid_path", "tolerance", "intent",
    ]

    with (VEC_DIR / "golden_vectors.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for v in vector_defs:
            best_id, best_score, best_bottleneck, valid, rows = select_path(
                v["candidates"], v["candidate_lens"], v["edges"], v["f_min_q016"], lut
            )
            if v.get("expect_id") is not None:
                assert best_id == v["expect_id"], (
                    f"{v['test_id']} expected path {v['expect_id']} but computed {best_id}; rows={rows}"
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
                "intent": v.get("note", ""),
            })

    print(f"Wrote {VEC_DIR / 'exp_lut.hex'}")
    print(f"Wrote {VEC_DIR / 'golden_vectors.csv'}")
    print(f"Vector count: {len(vector_defs)}")


if __name__ == "__main__":
    main()
