#!/usr/bin/env python3
"""Generate deterministic P5 B2 FDPE-mini LUT and exact test vectors."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path


getcontext().prec = 50
SCALE = 65535


def round_half_up(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def build_lut() -> list[int]:
    return [round_half_up((-Decimal(i) / Decimal(32)).exp() * SCALE) for i in range(256)]


def fdpe_reference(x_code: int, f_initial: int, tau_zero: int, lut: list[int]) -> tuple[int, int]:
    if tau_zero:
        return 0, 1
    if x_code >= 0x8000:
        return 0, 0
    index = x_code >> 7
    fraction = x_code & 0x7F
    y0 = lut[index]
    y1 = lut[index] if index == 255 else lut[index + 1]
    decay = (y0 * 128 + (y1 - y0) * fraction + 64) // 128
    return (f_initial * decay) >> 16, 0


def build_vectors(lut: list[int]) -> list[dict[str, int | str]]:
    raw: list[tuple[str, int, int, int]] = []
    raw.extend(("lut_boundary", 0, i << 7, 0xFFFF) for i in range(256))
    raw.extend(("interpolation_midpoint", 0, (i << 7) | 0x40, 0xF123) for i in range(256))
    raw.extend(
        [
            ("zero_tau", 1, 0x0000, 0xFFFF),
            ("x_at_8", 0, 0x8000, 0xFFFF),
            ("x_above_8", 0, 0xFFFF, 0xFFFF),
            ("zero_f_initial", 0, 0x1234, 0x0000),
            ("one_lsb_f_initial", 0, 0x0000, 0x0001),
            ("half_scale_f_initial", 0, 0x0000, 0x8000),
            ("general_interpolation", 0, 0x2A5B, 0xCDEF),
        ]
    )
    vectors = []
    for case_id, (category, tau_zero, x_code, f_initial) in enumerate(raw):
        expected, error = fdpe_reference(x_code, f_initial, tau_zero, lut)
        vectors.append(
            {
                "case_id": case_id,
                "category": category,
                "tau_zero": tau_zero,
                "x_uq4_12": x_code,
                "f_initial_unorm16": f_initial,
                "expected_fidelity_unorm16": expected,
                "expected_error": error,
            }
        )
    return vectors


BOARD_CASES = [
    (0, 0x0000, 0xFFFF),
    (0, 0x0000, 0x8000),
    (0, 0x0080, 0xFFFF),
    (0, 0x00C0, 0xF123),
    (0, 0x1000, 0xFFFF),
    (0, 0x2000, 0xE666),
    (0, 0x4000, 0xFFFF),
    (0, 0x7000, 0xFFFF),
    (0, 0x7F80, 0xFFFF),
    (0, 0x7FC0, 0xF123),
    (0, 0x8000, 0xFFFF),
    (0, 0xFFFF, 0xFFFF),
    (1, 0x0000, 0xFFFF),
    (0, 0x1234, 0x0000),
    (0, 0x0000, 0x0001),
    (0, 0x2A5B, 0xCDEF),
]


def packed(tau_zero: int, error: int, x_code: int, f_initial: int, expected: int) -> int:
    return (
        ((tau_zero & 1) << 49)
        | ((error & 1) << 48)
        | ((x_code & 0xFFFF) << 32)
        | ((f_initial & 0xFFFF) << 16)
        | (expected & 0xFFFF)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lut", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--mem", type=Path, required=True)
    parser.add_argument("--board-vh", type=Path, required=True)
    args = parser.parse_args()

    lut = build_lut()
    vectors = build_vectors(lut)
    for path in (args.lut, args.csv, args.mem, args.board_vh):
        path.parent.mkdir(parents=True, exist_ok=True)

    args.lut.write_text("".join(f"{value:04X}\n" for value in lut), encoding="ascii")
    with args.csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(vectors[0]))
        writer.writeheader()
        writer.writerows(vectors)
    args.mem.write_text(
        "".join(
            f"{packed(int(v['tau_zero']), int(v['expected_error']), int(v['x_uq4_12']), int(v['f_initial_unorm16']), int(v['expected_fidelity_unorm16'])):013X}\n"
            for v in vectors
        ),
        encoding="ascii",
    )

    board_lines = []
    for index, (tau_zero, x_code, f_initial) in enumerate(BOARD_CASES):
        expected, error = fdpe_reference(x_code, f_initial, tau_zero, lut)
        value = packed(tau_zero, error, x_code, f_initial, expected)
        board_lines.append(f"            5'd{index}: board_vector = 50'h{value:013X};\n")
    args.board_vh.write_text("".join(board_lines), encoding="ascii")

    print(f"P5_B2_FDPE_LUT_ENTRIES={len(lut)}")
    print(f"P5_B2_FDPE_VECTOR_COUNT={len(vectors)}")
    print(f"P5_B2_FDPE_BOARD_CASES={len(BOARD_CASES)}")


if __name__ == "__main__":
    main()
