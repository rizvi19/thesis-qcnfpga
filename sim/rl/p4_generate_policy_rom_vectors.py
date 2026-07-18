#!/usr/bin/env python3
"""Generate deterministic P4 Step 4 vectors from the frozen P3 policy ROM."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

from rl.p3_export import validate_inputs


REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_MEM = REPO_ROOT / "results/rl/p3_export/policy_rom.mem"
LAYOUT_PATH = REPO_ROOT / "results/rl/p3_export/rom_layout.json"
DEFAULT_CSV = REPO_ROOT / "sim/rl/p4_policy_rom_vectors.csv"
DEFAULT_RTL = REPO_ROOT / "sim/rl/p4_policy_rom_vectors.txt"

COLUMNS = (
    "case_id",
    "category",
    "rst",
    "en",
    "state_id",
    "expected_valid",
    "expected_proposed_action",
    "notes",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_frozen_policy():
    lines = POLICY_MEM.read_text(encoding="ascii").splitlines()
    if len(lines) != 256:
        raise RuntimeError(f"policy_rom.mem has {len(lines)} lines; expected 256")
    if any(re.fullmatch(r"[0-3]", line) is None for line in lines):
        raise RuntimeError("policy_rom.mem is not exactly one action hex digit 0..3 per line")
    words = tuple(int(line, 16) for line in lines)
    _q_table, frozen_policy, _codebook = validate_inputs()
    if words != tuple(frozen_policy):
        raise RuntimeError("policy_rom.mem differs from the frozen selected policy")
    if set(words) != {0, 1, 2, 3}:
        raise RuntimeError("frozen policy does not exercise all four actions")
    layout = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
    policy_layout = layout["policy_rom"]
    expected_layout = {
        "depth": 256,
        "useful_width_bits": 2,
        "file_hex_digits_per_word": 1,
        "address_order": "state_id_0_to_255",
    }
    for key, expected in expected_layout.items():
        if policy_layout.get(key) != expected:
            raise RuntimeError(f"policy ROM layout mismatch: {key}")
    return words


def build_vectors(policy):
    rows = []
    held_action = 0

    def append(category, rst, en, state_id, notes):
        nonlocal held_action
        if rst:
            expected_valid = 0
            held_action = 0
        elif en:
            expected_valid = 1
            held_action = policy[state_id]
        else:
            expected_valid = 0
        rows.append(
            {
                "case_id": len(rows),
                "category": category,
                "rst": rst,
                "en": en,
                "state_id": state_id,
                "expected_valid": expected_valid,
                "expected_proposed_action": held_action,
                "notes": notes,
            }
        )

    append("reset", 1, 1, 255, "reset dominates enable and address")
    for state_id in range(256):
        append("all_256_states", 0, 1, state_id, "exact frozen state-major policy lookup")
    append("enable_hold", 0, 0, 0, "valid clears and proposed action holds")
    append("reset", 1, 1, 255, "midstream reset clears the prior action")
    append("post_reset_read", 0, 1, 0, "first enabled read after reset")
    if len(rows) != 260:
        raise RuntimeError(f"Unexpected policy vector count: {len(rows)}")
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
                row["state_id"],
                row["expected_valid"],
                row["expected_proposed_action"],
            )
            handle.write(" ".join(str(value) for value in numeric) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--rtl-out", type=Path, default=DEFAULT_RTL)
    args = parser.parse_args()
    policy = read_frozen_policy()
    rows = build_vectors(policy)
    write_vectors(rows, args.csv_out, args.rtl_out)
    counts = {str(action): policy.count(action) for action in range(4)}
    print(f"P4_POLICY_ROM_VECTOR_COUNT={len(rows)}")
    print(f"P4_POLICY_ROM_MEM_SHA256={sha256(POLICY_MEM)}")
    print(f"P4_POLICY_ROM_ACTION_COUNTS={json.dumps(counts, sort_keys=True, separators=(',', ':'))}")
    print(f"P4_POLICY_ROM_CSV_SHA256={sha256(args.csv_out)}")
    print(f"P4_POLICY_ROM_RTL_VECTOR_SHA256={sha256(args.rtl_out)}")


if __name__ == "__main__":
    main()
