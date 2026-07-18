#!/usr/bin/env python3
"""Generate deterministic P4 Step 3 state-encoder unit vectors."""

import argparse
import csv
import hashlib
import json
from itertools import product
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "rl/config/p4_rtl_contract_v1.json"
DEFAULT_CSV = REPO_ROOT / "sim/rl/p4_state_encoder_vectors.csv"
DEFAULT_RTL = REPO_ROOT / "sim/rl/p4_state_encoder_vectors.txt"

COLUMNS = (
    "case_id",
    "category",
    "rst",
    "en",
    "min_key_occupancy_u16",
    "bottleneck_fidelity_u16",
    "offered_request_load_u16",
    "utilization_imbalance_u16",
    "expected_valid",
    "expected_state_id",
    "notes",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoded_bin(value, thresholds):
    return sum(value >= threshold for threshold in thresholds)


def encode_state(values, feature_order, thresholds):
    state_id = 0
    for feature_name, value in zip(feature_order, values):
        state_id = state_id * 4 + encoded_bin(value, thresholds[feature_name])
    return state_id


def build_vectors(contract):
    state = contract["state_interface"]
    feature_order = state["feature_order_msb_to_lsb"]
    thresholds = {
        name: tuple(state["features"][name]["threshold_codes"])
        for name in feature_order
    }
    representatives = {
        name: (0, *thresholds[name])
        for name in feature_order
    }

    rows = []
    held_state = 0

    def append(category, rst, en, values, notes):
        nonlocal held_state
        if rst:
            expected_valid = 0
            held_state = 0
        elif en:
            expected_valid = 1
            held_state = encode_state(values, feature_order, thresholds)
        else:
            expected_valid = 0
        rows.append(
            {
                "case_id": len(rows),
                "category": category,
                "rst": rst,
                "en": en,
                "min_key_occupancy_u16": values[0],
                "bottleneck_fidelity_u16": values[1],
                "offered_request_load_u16": values[2],
                "utilization_imbalance_u16": values[3],
                "expected_valid": expected_valid,
                "expected_state_id": held_state,
                "notes": notes,
            }
        )

    append("reset", 1, 1, (65535, 65535, 65535, 65535), "reset dominates enable and data")
    append("encoded_clip_low", 0, 1, (0, 0, 0, 0), "UNORM16 encoded lower endpoint")
    append("enable_hold", 0, 0, (65535, 65535, 65535, 65535), "valid clears and state output holds")
    append("encoded_clip_high", 0, 1, (65535, 65535, 65535, 65535), "UNORM16 encoded upper endpoint")
    append("reset", 1, 1, (65535, 65535, 65535, 65535), "midstream reset clears prior state")

    for bins in product(range(4), repeat=4):
        values = tuple(
            representatives[name][bin_index]
            for name, bin_index in zip(feature_order, bins)
        )
        append(
            "all_256_states",
            0,
            1,
            values,
            "representative lower-edge code for bins " + "/".join(map(str, bins)),
        )

    for feature_index, feature_name in enumerate(feature_order):
        for threshold_index, threshold in enumerate(thresholds[feature_name]):
            for category, delta in (
                ("threshold_below", -1),
                ("threshold_equal", 0),
                ("threshold_above", 1),
            ):
                values = [0, 0, 0, 0]
                values[feature_index] = threshold + delta
                append(
                    category,
                    0,
                    1,
                    tuple(values),
                    f"{feature_name} threshold {threshold_index + 1} code {threshold} delta {delta}",
                )

    if len(rows) != 297:
        raise RuntimeError(f"Unexpected vector count: {len(rows)}")
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
                row["min_key_occupancy_u16"],
                row["bottleneck_fidelity_u16"],
                row["offered_request_load_u16"],
                row["utilization_imbalance_u16"],
                row["expected_valid"],
                row["expected_state_id"],
            )
            handle.write(" ".join(str(value) for value in numeric) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--rtl-out", type=Path, default=DEFAULT_RTL)
    args = parser.parse_args()
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    rows = build_vectors(contract)
    write_vectors(rows, args.csv_out, args.rtl_out)
    print(f"P4_STATE_ENCODER_VECTOR_COUNT={len(rows)}")
    print(f"P4_STATE_ENCODER_CSV_SHA256={sha256(args.csv_out)}")
    print(f"P4_STATE_ENCODER_RTL_VECTOR_SHA256={sha256(args.rtl_out)}")


if __name__ == "__main__":
    main()
