#!/usr/bin/env python3
"""Generate deterministic P4 Step 5 vectors from the frozen profile ROM."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

from rl.p3_export import decode_profile, encode_profile, validate_inputs


REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE_MEM = REPO_ROOT / "results/rl/p3_export/profile_rom.mem"
LAYOUT_PATH = REPO_ROOT / "results/rl/p3_export/rom_layout.json"
DEFAULT_CSV = REPO_ROOT / "sim/rl/p4_profile_rom_vectors.csv"
DEFAULT_RTL = REPO_ROOT / "sim/rl/p4_profile_rom_vectors.txt"

COLUMNS = (
    "case_id",
    "category",
    "rst",
    "en",
    "selected_action",
    "expected_valid",
    "expected_profile_payload_hex",
    "expected_profile_payload_decimal",
    "notes",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_frozen_profiles():
    lines = PROFILE_MEM.read_text(encoding="ascii").splitlines()
    if len(lines) != 4:
        raise RuntimeError(f"profile_rom.mem has {len(lines)} lines; expected 4")
    if any(re.fullmatch(r"[0-3][0-9A-F]{4}", line) is None for line in lines):
        raise RuntimeError("profile_rom.mem is not exactly four uppercase five-hex-digit 18-bit words")
    words = tuple(int(line, 16) for line in lines)
    _q_table, _policy, codebook = validate_inputs()
    expected = tuple(encode_profile(profile) for profile in codebook["profiles"])
    if words != expected:
        raise RuntimeError("profile_rom.mem differs from the frozen profile codebook")
    if len(set(words)) != 4 or any(word >= (1 << 18) for word in words):
        raise RuntimeError("profile payloads are not four distinct 18-bit words")
    for word, profile in zip(words, codebook["profiles"]):
        alphas, ratios = decode_profile(word)
        expected_alphas = tuple(int(round(float(value) * 2)) for value in profile["alphas"])
        expected_ratios = tuple(int(value) for value in profile["lambda_tch_hw_ratio"])
        if alphas != expected_alphas or ratios != expected_ratios:
            raise RuntimeError("profile payload does not round-trip to frozen coefficients")
    layout = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))["profile_rom"]
    checks = {
        "depth": 4,
        "payload_bits": 18,
        "file_hex_digits_per_word": 5,
    }
    for key, expected_value in checks.items():
        if layout.get(key) != expected_value:
            raise RuntimeError(f"profile ROM layout mismatch: {key}")
    if len(layout.get("field_order_msb_to_lsb", [])) != 7:
        raise RuntimeError("profile field order is not frozen to seven fields")
    return words


def build_vectors(words):
    rows = []
    held_payload = 0

    def append(category, rst, en, action, notes):
        nonlocal held_payload
        if rst:
            expected_valid = 0
            held_payload = 0
        elif en:
            expected_valid = 1
            held_payload = words[action]
        else:
            expected_valid = 0
        rows.append(
            {
                "case_id": len(rows),
                "category": category,
                "rst": rst,
                "en": en,
                "selected_action": action,
                "expected_valid": expected_valid,
                "expected_profile_payload_hex": f"{held_payload:05X}",
                "expected_profile_payload_decimal": held_payload,
                "notes": notes,
            }
        )

    append("reset", 1, 1, 3, "reset dominates enable and action")
    for action in range(4):
        append("all_four_actions", 0, 1, action, "exact frozen action-major profile lookup")
    append("enable_hold", 0, 0, 0, "valid clears and payload holds")
    append("reset", 1, 1, 3, "midstream reset clears the prior payload")
    append("post_reset_read", 0, 1, 0, "first enabled read after reset")
    if len(rows) != 8:
        raise RuntimeError(f"Unexpected profile vector count: {len(rows)}")
    return rows


def write_vectors(rows, csv_path, rtl_path):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    rtl_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with rtl_path.open("w", encoding="utf-8", newline="") as handle:
        for row in rows:
            numeric = (
                row["case_id"],
                row["rst"],
                row["en"],
                row["selected_action"],
                row["expected_valid"],
                row["expected_profile_payload_decimal"],
            )
            handle.write(" ".join(str(value) for value in numeric) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--rtl-out", type=Path, default=DEFAULT_RTL)
    args = parser.parse_args()
    words = read_frozen_profiles()
    rows = build_vectors(words)
    write_vectors(rows, args.csv_out, args.rtl_out)
    print(f"P4_PROFILE_ROM_VECTOR_COUNT={len(rows)}")
    print(f"P4_PROFILE_ROM_MEM_SHA256={sha256(PROFILE_MEM)}")
    print(f"P4_PROFILE_ROM_PAYLOADS={json.dumps([f'{word:05X}' for word in words], separators=(',', ':'))}")
    print(f"P4_PROFILE_ROM_TOTAL_USEFUL_BITS={len(words) * 18}")
    print(f"P4_PROFILE_ROM_CSV_SHA256={sha256(args.csv_out)}")
    print(f"P4_PROFILE_ROM_RTL_VECTOR_SHA256={sha256(args.rtl_out)}")


if __name__ == "__main__":
    main()
