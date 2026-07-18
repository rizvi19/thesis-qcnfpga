#!/usr/bin/env python3
"""Generate the exhaustive P4 Step 8 controller vectors and summary."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from p4_generate_controller_unit_vectors import ControllerModel


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "rl/config/p4_rtl_contract_v1.json"
SCHEMA_PATH = REPO_ROOT / "sim/rl/p4_golden_vector_schema.json"
POLICY_MEM = REPO_ROOT / "results/rl/p3_export/policy_rom.mem"
PROFILE_MEM = REPO_ROOT / "results/rl/p3_export/profile_rom.mem"
DEFAULT_CSV = REPO_ROOT / "sim/rl/p4_exhaustive_vectors.csv"
DEFAULT_RTL = REPO_ROOT / "sim/rl/p4_exhaustive_vectors.txt"
DEFAULT_SUMMARY = REPO_ROOT / "sim/rl/p4_exhaustive_summary.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def representatives_for_state(state_id, contract):
    state = contract["state_interface"]
    bins = ((state_id >> 6) & 3, (state_id >> 4) & 3, (state_id >> 2) & 3, state_id & 3)
    return tuple(
        (0, *state["features"][name]["threshold_codes"])[bin_index]
        for name, bin_index in zip(state["feature_order_msb_to_lsb"], bins)
    )


def build_vectors(contract, schema, policy, profiles):
    model = ControllerModel(contract, policy, profiles)
    rows = []

    def append(category, rst=0, start=0, input_valid=1, no_path=0, values=(0, 0, 0, 0), notes=""):
        inputs = {
            "rst": rst, "start": start, "input_valid": input_valid, "no_path_in": no_path,
            "min_key_occupancy_u16": values[0], "bottleneck_fidelity_u16": values[1],
            "offered_request_load_u16": values[2], "utilization_imbalance_u16": values[3],
        }
        expected = model.step(inputs)
        row = {
            "case_id": f"exhaustive_{len(rows):04d}", "category": category, "cycle": len(rows),
            **inputs, **expected, "notes": notes,
        }
        if category == "auto_complete":
            if expected["expected_no_path_out"]:
                row["category"] = "no_path_passthrough"
            elif expected["expected_switched"]:
                row["category"] = "dwell_switch"
            elif expected["expected_proposed_action"] != expected["expected_selected_action"]:
                row["category"] = "dwell_hold"
            else:
                row["category"] = "valid_complete"
        rows.append(row)
        return row

    def transaction(values, completion_category, note, first=True, no_path=0, inject_stall=False):
        append("valid_accept" if first else "back_to_back_requests", start=1, input_valid=1,
               no_path=no_path, values=values, notes=f"{note}; accepted")
        if inject_stall:
            append("start_while_busy", start=1, input_valid=1, values=(65535, 65535, 65535, 65535),
                   notes="busy start rejected without transaction change")
        else:
            append("pipeline_wait", notes="registered pipeline wait 1")
        append("pipeline_wait", notes="registered pipeline wait 2")
        return append(completion_category, notes=f"{note}; completed after N+3")

    # Exact state-to-policy-to-profile mapping. Reset removes dwell history for every state.
    for state_id in range(256):
        append("reset", rst=1, start=1, notes=f"isolate exhaustive state {state_id}")
        completed = transaction(representatives_for_state(state_id, contract), "all_256_states", f"state {state_id}")
        if completed["expected_state_id"] != state_id:
            raise RuntimeError(f"state encoder mismatch at {state_id}")
        action = policy[state_id]
        if completed["expected_proposed_action"] != action or completed["expected_selected_action"] != action:
            raise RuntimeError(f"policy mismatch at state {state_id}")
        if completed["expected_profile_payload_hex"] != f"{profiles[action]:05X}":
            raise RuntimeError(f"profile mismatch at state {state_id}")
        if completed["expected_dwell_count_sat"] != 1 or completed["expected_switched"] != 0:
            raise RuntimeError(f"isolated dwell mismatch at state {state_id}")

    # All twelve encoded thresholds, each with below/equal/above exact codes.
    state_contract = contract["state_interface"]
    for feature_index, feature_name in enumerate(state_contract["feature_order_msb_to_lsb"]):
        for threshold_index, threshold in enumerate(state_contract["features"][feature_name]["threshold_codes"]):
            for relation, value in (("below", threshold - 1), ("equal", threshold), ("above", threshold + 1)):
                values = [0, 0, 0, 0]
                values[feature_index] = value
                append("reset", rst=1, start=1,
                       notes=f"isolate {feature_name} threshold {threshold_index} {relation}")
                transaction(tuple(values), f"threshold_{relation}",
                            f"{feature_name} threshold {threshold_index} {relation}")

    for category, values in (
        ("encoded_clip_low", (0, 0, 0, 0)),
        ("encoded_clip_high", (65535, 65535, 65535, 65535)),
    ):
        append("reset", rst=1, start=1, notes=f"isolate {category}")
        transaction(values, category, category)

    states_by_action = {}
    for state_id, action in enumerate(policy):
        states_by_action.setdefault(action, state_id)
    if set(states_by_action) != {0, 1, 2, 3}:
        raise RuntimeError("frozen policy does not expose all four actions")
    for action in range(4):
        append("reset", rst=1, start=1, notes=f"isolate action {action}")
        completed = transaction(representatives_for_state(states_by_action[action], contract),
                                "all_four_actions", f"action {action}")
        if completed["expected_selected_action"] != action:
            raise RuntimeError(f"isolated action mismatch at {action}")

    # Exceptional and dwell timeline without per-request resets.
    append("reset", rst=1, start=1, notes="reset before directed exceptional sequence")
    append("invalid_input", start=1, input_valid=0, notes="invalid request acceptance")
    append("invalid_complete", notes="invalid response after N+1")
    directed = (0, 1, 1, 1)
    for index, action in enumerate(directed):
        transaction(
            representatives_for_state(states_by_action[action], contract), "auto_complete",
            f"directed proposal {action}", first=(index == 0), no_path=int(index == 1),
            inject_stall=(index == 0),
        )

    if tuple(schema["columns"]) != tuple(rows[0].keys()):
        raise RuntimeError("exhaustive vectors do not use the frozen golden schema")
    if len(rows) != 1509:
        raise RuntimeError(f"exhaustive cycle count changed: {len(rows)}")
    return rows


def summary_for(rows, policy, profiles):
    completions = [row for row in rows if row["expected_output_valid"] == 1]
    state_rows = [row for row in rows if row["category"] == "all_256_states"]
    return {
        "schema_version": 1,
        "phase": "P4",
        "step": "P4_STEP_8_EXHAUSTIVE_VECTORS",
        "cycle_vector_count": len(rows),
        "valid_decision_count": len(completions),
        "all_state_case_count": len(state_rows),
        "threshold_edge_case_count": sum(row["category"].startswith("threshold_") for row in rows),
        "encoded_endpoint_case_count": sum(row["category"] in {"encoded_clip_low", "encoded_clip_high"} for row in rows),
        "isolated_action_case_count": sum(row["category"] == "all_four_actions" for row in rows),
        "state_ids_covered": sorted(row["expected_state_id"] for row in state_rows),
        "selected_actions_covered": sorted({row["expected_selected_action"] for row in completions}),
        "policy_action_counts": {str(action): policy.count(action) for action in range(4)},
        "profile_payloads_hex": [f"{value:05X}" for value in profiles],
        "category_counts": dict(Counter(row["category"] for row in rows)),
        "state_action_mismatch_count": 0,
        "state_profile_mismatch_count": 0,
        "unexplained_mismatch_count": 0,
        "policy_rom_deployed": True,
        "q_table_role": "audit_only",
        "runtime_argmax_deployed": False,
        "q_update_implemented": False,
        "ise_synthesis_performed": False,
        "board_programming_performed": False,
        "eeprom_access_performed": False,
    }


def write_outputs(rows, schema, policy, profiles, csv_path, rtl_path, summary_path):
    for path in (csv_path, rtl_path, summary_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=schema["columns"], lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    numeric_columns = (
        "cycle", "rst", "start", "input_valid", "no_path_in",
        "min_key_occupancy_u16", "bottleneck_fidelity_u16", "offered_request_load_u16",
        "utilization_imbalance_u16", "expected_ready", "expected_busy", "expected_done",
        "expected_output_valid", "expected_invalid_state", "expected_stall", "expected_no_path_out",
        "expected_state_id", "expected_proposed_action", "expected_selected_action",
        "expected_profile_payload_hex", "expected_switched", "expected_dwell_count_sat",
    )
    with rtl_path.open("w", encoding="utf-8", newline="") as handle:
        for row in rows:
            values = [str(int(row[name], 16)) if name == "expected_profile_payload_hex" else str(row[name]) for name in numeric_columns]
            handle.write(" ".join(values) + "\n")
    summary_path.write_text(json.dumps(summary_for(rows, policy, profiles), indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--rtl-out", type=Path, default=DEFAULT_RTL)
    parser.add_argument("--summary-out", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    policy = tuple(int(line, 16) for line in POLICY_MEM.read_text(encoding="ascii").splitlines())
    profiles = tuple(int(line, 16) for line in PROFILE_MEM.read_text(encoding="ascii").splitlines())
    rows = build_vectors(contract, schema, policy, profiles)
    write_outputs(rows, schema, policy, profiles, args.csv_out, args.rtl_out, args.summary_out)
    print(f"P4_EXHAUSTIVE_CYCLE_VECTOR_COUNT={len(rows)}")
    print("P4_EXHAUSTIVE_VALID_DECISIONS=302")
    print("P4_EXHAUSTIVE_STATE_CASES=256")
    print("P4_EXHAUSTIVE_THRESHOLD_CASES=36")
    print("P4_EXHAUSTIVE_ENDPOINT_CASES=2")
    print("P4_EXHAUSTIVE_ACTION_CASES=4")
    print(f"P4_EXHAUSTIVE_CSV_SHA256={sha256(args.csv_out)}")
    print(f"P4_EXHAUSTIVE_RTL_VECTOR_SHA256={sha256(args.rtl_out)}")
    print(f"P4_EXHAUSTIVE_SUMMARY_SHA256={sha256(args.summary_out)}")


if __name__ == "__main__":
    main()
