#!/usr/bin/env python3
"""Validate the frozen P6 same-board experiment contract."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
CONTRACT = REPO / "rl/config/p6_same_board_experiment_contract_v1.json"
CONTRACT_DIR = REPO / "results/nexys3/p6_contract"
AUTHORITY = REPO / "evidence/nexys3/p6_step2_contract_freeze/authority_sha256.txt"

EXPECTED_HEAD = "e701dfa15d01938d85b281ab38bd07f6368d37e4"
EXPECTED_MODES = ["H0", "H1", "H2", "H3", "H4"]
EXPECTED_TAGS = ["n3_h0", "n3_h1", "n3_h2", "n3_h3", "n3_h4"]
EXPECTED_RESULT_FIELDS = [
    "test_id",
    "policy_id",
    "state_id",
    "profile_id",
    "selected_path",
    "score",
    "bottleneck_fidelity",
    "cycles",
    "status",
]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def csv_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as f:
        return next(csv.reader(f))

def require(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS {label}")

def main() -> int:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))

    require(data["schema_version"] == 1, "schema_version")
    require(data["phase"] == "P6", "phase")
    require(data["source_checkpoint"] == EXPECTED_HEAD, "source_checkpoint")
    require(data["branch"] == "rl-nexys3-adaptive", "branch")
    require(data["target"]["part"] == "XC6SLX16-2-CSG324", "target_part")
    require(data["target"]["physical_clock_hz"] == 100_000_000, "physical_clock_hz")
    require(data["target"]["physical_clock_period_ns"] == 10, "physical_clock_period_ns")

    builds = data["builds"]
    require([b["mode"] for b in builds] == EXPECTED_MODES, "mode_order")
    require([b["build_tag"] for b in builds] == EXPECTED_TAGS, "build_tag_order")
    require([b["policy_id"] for b in builds] == list(range(5)), "policy_ids")
    require(len({b["build_tag"] for b in builds}) == 5, "unique_build_tags")

    common = data["common_shell"]
    for key in (
        "same_external_shell",
        "same_numeric_widths",
        "same_arithmetic",
        "same_replay",
        "same_ucf",
        "same_handshake",
        "same_measurement_boundary",
        "independent_synthesis_per_mode",
    ):
        require(common[key] is True, f"common_shell_{key}")

    h4 = data["h4"]
    require(h4["training"] == "offline", "h4_offline_training")
    require(h4["online_learning"] is False, "h4_no_online_learning")
    require(h4["q_update"] is False, "h4_no_q_update")
    require(h4["runtime_argmax"] is False, "h4_no_runtime_argmax")
    require(h4["minimum_dwell_decisions"] == 3, "h4_dwell")
    require(
        h4["approved_label"] == "reinforcement-learned adaptive profile controller",
        "h4_approved_label",
    )

    replay = data["replay"]
    require(replay["tier_a"]["rows"] == 20, "tier_a_rows")
    require(replay["tier_a"]["test_ids"] == list(range(20)), "tier_a_test_ids")
    require(replay["tier_b"]["rows"] == 64, "tier_b_rows")
    require(replay["tier_b"]["seed"] == 26072026, "tier_b_seed")
    require(replay["tier_b"]["tuning_after_hash"] is False, "no_tuning_after_hash")
    require(replay["tier_b"]["final_sha256"] is None, "replay_hash_deferred_to_step3")

    require(data["result_fields"] == EXPECTED_RESULT_FIELDS, "result_field_order")
    require(data["measurement"]["uart_host_excluded"] is True, "uart_host_excluded")
    require(data["measurement"]["achieved_fmax_role"] == "implementation_capacity_not_physical_board_clock", "fmax_boundary")
    require(data["correctness"]["mandatory_exact_vector_match_percent"] == 100, "exact_vector_gate")

    require(
        csv_header(CONTRACT_DIR / "board_results_schema.csv") == EXPECTED_RESULT_FIELDS,
        "board_schema_header",
    )
    require(
        csv_header(CONTRACT_DIR / "golden_results_schema.csv") == EXPECTED_RESULT_FIELDS,
        "golden_schema_header",
    )

    expected_build_header = [
        "build_tag","policy_id","mode","source_commit","replay_sha256","ucf_sha256",
        "bitstream_bytes","bitstream_sha256","slices","luts","ffs","brams","dsps",
        "minimum_period_ns","achieved_fmax_mhz","timing_errors","programming_device",
        "jtag_id","raw_log","parsed_csv","golden_comparison","physical_observation","status"
    ]
    require(
        csv_header(CONTRACT_DIR / "build_manifest_schema.csv") == expected_build_header,
        "build_schema_header",
    )

    expected_replay_header = [
        "replay_order","test_id","replay_id","sequence_class","seed","src","dst",
        "min_key_occupancy_u16","bottleneck_fidelity_state_u16",
        "offered_request_load_u16","utilization_imbalance_state_u16",
        "c0_valid","c0_cost","c0_fidelity","c0_utilization","c0_hops","c0_slot",
        "c1_valid","c1_cost","c1_fidelity","c1_utilization","c1_hops","c1_slot",
        "input_valid","expected_status","held_out"
    ]
    require(
        csv_header(CONTRACT_DIR / "replay_manifest_schema.csv") == expected_replay_header,
        "replay_schema_header",
    )

    lines = [
        line.strip()
        for line in AUTHORITY.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    require(len(lines) == 11, "authority_manifest_count")

    for line in lines:
        digest, rel = line.split(None, 1)
        path = REPO / rel
        require(path.is_file(), f"authority_present:{rel}")
        require(sha256(path) == digest, f"authority_hash:{rel}")

    print("P6_STEP2_CONTRACT_VALIDATION=PASS")
    print("P6_STEP2_AUTHORITY_FILES=11_OF_11_PASS")
    print("P6_STEP2_MODES=5_OF_5_PASS")
    print("P6_STEP2_RESULT_SCHEMA=EXACT_PASS")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"P6_STEP2_CONTRACT_VALIDATION=FAIL: {exc}", file=sys.stderr)
        raise
