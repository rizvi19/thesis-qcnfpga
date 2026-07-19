#!/usr/bin/env python3
"""Generate deterministic, bit-exact P5 B3 SKAG-mini vectors."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


PROFILES = (0x13329, 0x1B516, 0x14399, 0x0A2A5)
INFINITY = 0xFFFFFFFF
MAX_FINITE = 0xFFFFFFFE


def alphas(payload: int) -> tuple[int, int, int, int]:
    return tuple((payload >> shift) & 7 for shift in (15, 12, 9, 6))


def round_ratio(numerator: int, denominator: int) -> int:
    return (2 * numerator + denominator) // (2 * denominator)


def reference(edge: tuple[int, int, int, int], payload: int) -> tuple[int, int, tuple[int, ...]]:
    key_count, fidelity, key_rate, qber = edge
    if key_count == 0 or fidelity == 0 or key_rate == 0:
        return INFINITY, 0, ()
    a1, a2, a3, a4 = alphas(payload)
    terms = (
        round_ratio(a1 * 65536, 2 * key_count),
        round_ratio(a2 * 65535 * 65536, 2 * fidelity),
        round_ratio(a3 * 128 * 65536, key_rate),
        round_ratio(a4 * qber * 65536, 2 * 65535),
    )
    total = 0
    for term in terms:
        total = min(MAX_FINITE, total + term)
    return total, 1, terms


def edge_word(edge: tuple[int, int, int, int]) -> int:
    k, f, rate, qber = edge
    return (k << 48) | (f << 32) | (rate << 16) | qber


def classify(edge: tuple[int, int, int, int], weight: int, feasible: int) -> str:
    if not feasible:
        zero_names = [name for name, value in zip(("key", "fidelity", "rate"), edge[:3]) if value == 0]
        return "infeasible_zero_" + "_".join(zero_names)
    if weight == MAX_FINITE:
        return "finite_saturation"
    return "finite_exact"


def make_edges() -> list[tuple[int, int, int, int]]:
    directed_ring6 = [
        (16, 65535, 256, 0), (15, 64225, 384, 328),
        (14, 62914, 512, 655), (13, 61603, 640, 983),
        (12, 60292, 768, 1311), (11, 58982, 896, 1638),
        (10, 57671, 1024, 1966), (9, 56360, 1152, 2294),
        (8, 55049, 1280, 2621), (7, 53739, 1408, 2949),
        (6, 52428, 1536, 3277), (5, 51117, 1664, 3604),
    ]
    boundaries = [
        (0, 65535, 256, 0), (1, 0, 256, 0), (1, 65535, 0, 0),
        (0, 0, 0, 65535), (1, 1, 1, 65535), (1, 2, 1, 65534),
        (1, 65535, 1, 0), (65535, 1, 65535, 65535),
        (65535, 65535, 65535, 0), (2, 32768, 128, 32768),
        (3, 58982, 256, 6554), (16, 65535, 65535, 65535),
    ]
    edges = directed_ring6 + boundaries
    rng = random.Random(0xB3A62026)
    choices_k = (1, 2, 3, 4, 7, 8, 15, 16, 31, 255, 1024, 65535)
    choices_f = (1, 2, 3, 32767, 32768, 58982, 65534, 65535)
    choices_r = (1, 2, 3, 127, 128, 255, 256, 257, 1024, 65535)
    choices_q = (0, 1, 2, 32767, 32768, 65534, 65535)
    for _ in range(240):
        edges.append((rng.choice(choices_k), rng.choice(choices_f), rng.choice(choices_r), rng.choice(choices_q)))
    return edges


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--mem", type=Path, required=True)
    parser.add_argument("--board-vh", type=Path, required=True)
    args = parser.parse_args()

    rows = []
    for profile_index, payload in enumerate(PROFILES):
        for edge_index, edge in enumerate(make_edges()):
            weight, feasible, terms = reference(edge, payload)
            rows.append({
                "case_id": len(rows),
                "category": classify(edge, weight, feasible),
                "profile_index": profile_index,
                "profile_payload_hex": f"{payload:05X}",
                "key_count": edge[0],
                "fidelity_unorm16": edge[1],
                "key_rate_uq8_8": edge[2],
                "qber_unorm16": edge[3],
                "expected_weight_uq16_16_hex": f"{weight:08X}",
                "expected_feasible": feasible,
                "terms_hex": ":".join(f"{term:X}" for term in terms),
            })

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with args.csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with args.mem.open("w", encoding="ascii") as handle:
        for row in rows:
            edge = (int(row["key_count"]), int(row["fidelity_unorm16"]),
                    int(row["key_rate_uq8_8"]), int(row["qber_unorm16"]))
            packed = edge_word(edge)
            packed = (packed << 18) | int(row["profile_payload_hex"], 16)
            packed = (packed << 32) | int(row["expected_weight_uq16_16_hex"], 16)
            packed = (packed << 1) | int(row["expected_feasible"])
            handle.write(f"{packed:029X}\n")

    board_indices = (0, 1, 2, 4, 5, 8, 10, 11, 272, 273, 276, 280, 544, 548, 816, 820)
    with args.board_vh.open("w", encoding="ascii") as handle:
        for board_index, row_index in enumerate(board_indices):
            row = rows[row_index]
            edge = (int(row["key_count"]), int(row["fidelity_unorm16"]),
                    int(row["key_rate_uq8_8"]), int(row["qber_unorm16"]))
            packed = edge_word(edge)
            packed = (packed << 18) | int(row["profile_payload_hex"], 16)
            packed = (packed << 32) | int(row["expected_weight_uq16_16_hex"], 16)
            packed = (packed << 1) | int(row["expected_feasible"])
            handle.write(f"                5'd{board_index}: board_vector = 115'h{packed:029X};\n")

    categories = {row["category"] for row in rows}
    assert any(name.startswith("infeasible") for name in categories)
    assert "finite_saturation" in categories
    assert "finite_exact" in categories
    print(f"P5_B3_SKAG_VECTOR_COUNT={len(rows)}")
    print("P5_B3_SKAG_PROFILES=4_OF_4_EXACT")
    print("P5_B3_SKAG_INFEASIBLE_COVERAGE=PASS")
    print("P5_B3_SKAG_SATURATION_COVERAGE=PASS")


if __name__ == "__main__":
    main()
