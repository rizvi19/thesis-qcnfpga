#!/usr/bin/env python3
"""Generate frozen-H4 and directed cycle vectors for P4 Step 7."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

from rl.dwell_controller import MinimumDwellController
from rl.mdp_contract import CONTRACT as MDP_CONTRACT
from rl.ring6_environment import Ring6Environment
from rl.trace_generator import build_manual_trace, canonical_trace_bytes, generate_trace

from p4_generate_controller_unit_vectors import ControllerModel


REPO_ROOT = Path(__file__).resolve().parents[2]
RTL_CONTRACT_PATH = REPO_ROOT / "rl/config/p4_rtl_contract_v1.json"
SCHEMA_PATH = REPO_ROOT / "sim/rl/p4_golden_vector_schema.json"
TRACE_MANIFEST_PATH = REPO_ROOT / "results/rl/p2_environment/trace_manifest.json"
POLICY_MEM = REPO_ROOT / "results/rl/p3_export/policy_rom.mem"
PROFILE_MEM = REPO_ROOT / "results/rl/p3_export/profile_rom.mem"
DEFAULT_CYCLE_CSV = REPO_ROOT / "sim/rl/p4_integrated_trace_vectors.csv"
DEFAULT_RTL = REPO_ROOT / "sim/rl/p4_integrated_trace_vectors.txt"
DEFAULT_TRACE_CSV = REPO_ROOT / "sim/rl/p4_h4_frozen_trace_timeline.csv"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trace_sha256(trace):
    return hashlib.sha256(canonical_trace_bytes(trace)).hexdigest()


def representatives_for_state(state_id, rtl_contract):
    state = rtl_contract["state_interface"]
    values = []
    bins = ((state_id >> 6) & 3, (state_id >> 4) & 3, (state_id >> 2) & 3, state_id & 3)
    for name, bin_index in zip(state["feature_order_msb_to_lsb"], bins):
        thresholds = tuple(state["features"][name]["threshold_codes"])
        values.append((0, *thresholds)[bin_index])
    return tuple(values)


def replay_trace(partition, seed, trace, policy, profiles, expected_trace_hash):
    actual_trace_hash = trace_sha256(trace)
    if actual_trace_hash != expected_trace_hash:
        raise RuntimeError(f"{partition} trace hash differs from the frozen manifest")
    environment = Ring6Environment(trace)
    controller = MinimumDwellController(policy, 3)
    rows = []
    previous_selected = None
    while not environment.done:
        state_id = environment.current_state_id()
        proposed = policy[state_id]
        selected = controller.choose_action(state_id)
        switched = int(previous_selected is not None and selected != previous_selected)
        result = environment.step(selected)
        if result.state_id != state_id or result.action_id != selected:
            raise RuntimeError("environment transition differs from the H4 decision")
        rows.append({
            "trace_id": trace.trace_id,
            "partition": partition,
            "seed": "" if seed is None else seed,
            "trace_sha256": actual_trace_hash,
            "trace_index": result.trace_index,
            "state_id": state_id,
            "proposed_action": proposed,
            "selected_action": selected,
            "profile_payload_hex": f"{profiles[selected]:05X}",
            "dwell_count_sat": min(3, controller.dwell_count),
            "switched": switched,
            "success": int(result.success),
            "no_path": int(not result.success),
            "selected_path": "" if result.selected_path is None else "-".join(map(str, result.selected_path)),
            "reward_total": f"{result.reward.total:.12f}",
            "next_state_id": "" if result.next_state_id is None else result.next_state_id,
            "done": int(result.done),
        })
        previous_selected = selected
    return rows


def frozen_h4_timelines(policy, profiles):
    manifest = json.loads(TRACE_MANIFEST_PATH.read_text(encoding="utf-8"))
    manual = build_manual_trace()
    manual_hash = manifest["manual_trace"]["trace_sha256"]
    manual_rows = replay_trace("manual", None, manual, policy, profiles, manual_hash)
    test_seed = int(MDP_CONTRACT["partitions"]["test_seeds"][0])
    length = int(MDP_CONTRACT["partitions"]["episode_length"])
    test_entry = next(
        item for item in manifest["traces"]
        if item["partition"] == "test" and int(item["seed"]) == test_seed
    )
    test_trace = generate_trace(test_seed, length)
    test_rows = replay_trace("test", test_seed, test_trace, policy, profiles, test_entry["sha256"])
    if len(manual_rows) != 8 or len(test_rows) != 512:
        raise RuntimeError("frozen H4 trace lengths changed")
    return manual_rows, test_rows, test_seed


def build_cycle_vectors(rtl_contract, schema, policy, profiles, manual_rows, test_rows):
    model = ControllerModel(rtl_contract, policy, profiles)
    rows = []

    def append(category, rst=0, start=0, input_valid=1, no_path=0, values=(0, 0, 0, 0), notes=""):
        inputs = {
            "rst": rst,
            "start": start,
            "input_valid": input_valid,
            "no_path_in": no_path,
            "min_key_occupancy_u16": values[0],
            "bottleneck_fidelity_u16": values[1],
            "offered_request_load_u16": values[2],
            "utilization_imbalance_u16": values[3],
        }
        expected = model.step(inputs)
        row = {
            "case_id": f"integrated_{len(rows):04d}",
            "category": category,
            "cycle": len(rows),
            **inputs,
            **expected,
            "notes": notes,
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

    def transaction(state_id, no_path, first, note, inject_stall=False, expected_trace=None):
        values = representatives_for_state(state_id, rtl_contract)
        accept_category = "valid_accept" if first else "back_to_back_requests"
        append(accept_category, start=1, input_valid=1, no_path=no_path, values=values, notes=note)
        if inject_stall:
            append("start_while_busy", start=1, input_valid=1,
                   values=representatives_for_state((state_id + 1) & 255, rtl_contract),
                   notes="busy request rejected; active transaction preserved")
        else:
            append("pipeline_wait", notes="registered pipeline wait 1")
        append("pipeline_wait", notes="registered pipeline wait 2")
        completed = append("auto_complete", notes=f"{note}; completion after N+3")
        if expected_trace is not None:
            expected = {
                "expected_state_id": str(expected_trace["state_id"]),
                "expected_proposed_action": str(expected_trace["proposed_action"]),
                "expected_selected_action": str(expected_trace["selected_action"]),
                "expected_profile_payload_hex": expected_trace["profile_payload_hex"],
                "expected_dwell_count_sat": str(expected_trace["dwell_count_sat"]),
                "expected_switched": str(expected_trace["switched"]),
                "expected_no_path_out": str(expected_trace["no_path"]),
            }
            for key, value in expected.items():
                if str(completed[key]) != value:
                    raise RuntimeError(
                        f"cycle model differs from frozen H4 trace at {note}: "
                        f"{key}={completed[key]} expected={value}"
                    )

    append("reset", rst=1, start=1, notes="reset before manual frozen H4 trace")
    for index, trace_row in enumerate(manual_rows):
        transaction(
            int(trace_row["state_id"]), int(trace_row["no_path"]), index == 0,
            f"manual H4 trace decision {index}", inject_stall=(index == 2), expected_trace=trace_row,
        )
    append("invalid_input", start=1, input_valid=0, notes="invalid request does not advance H4 dwell")
    append("invalid_complete", notes="invalid response after N+1")

    append("reset", rst=1, start=1, notes="independent reset before locked test trace")
    for index, trace_row in enumerate(test_rows):
        transaction(
            int(trace_row["state_id"]), int(trace_row["no_path"]), index == 0,
            f"locked test H4 trace decision {index}", inject_stall=(index == 17), expected_trace=trace_row,
        )

    append("reset", rst=1, start=1, notes="independent reset before directed exception trace")
    states_by_action = {}
    for state_id, action in enumerate(policy):
        states_by_action.setdefault(action, state_id)
    if set(states_by_action) != {0, 1, 2, 3}:
        raise RuntimeError("frozen policy does not expose all actions")
    directed_actions = (0, 1, 1, 1, 1, 2, 2, 2, 3, 3)
    for index, action in enumerate(directed_actions):
        transaction(
            states_by_action[action], int(index == 7), index == 0,
            f"directed proposal action {action}", expected_trace=None,
        )

    if tuple(schema["columns"]) != tuple(rows[0].keys()):
        raise RuntimeError("integrated vectors do not use the frozen golden schema")
    if len(rows) != 2125:
        raise RuntimeError(f"integrated vector count changed: {len(rows)}")
    return rows


TRACE_COLUMNS = (
    "trace_id", "partition", "seed", "trace_sha256", "trace_index", "state_id",
    "proposed_action", "selected_action", "profile_payload_hex", "dwell_count_sat",
    "switched", "success", "no_path", "selected_path", "reward_total",
    "next_state_id", "done",
)


def write_outputs(cycle_rows, trace_rows, schema, cycle_csv, rtl_path, trace_csv):
    for path in (cycle_csv, rtl_path, trace_csv):
        path.parent.mkdir(parents=True, exist_ok=True)
    with cycle_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=schema["columns"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(cycle_rows)
    numeric_columns = (
        "cycle", "rst", "start", "input_valid", "no_path_in",
        "min_key_occupancy_u16", "bottleneck_fidelity_u16", "offered_request_load_u16",
        "utilization_imbalance_u16", "expected_ready", "expected_busy", "expected_done",
        "expected_output_valid", "expected_invalid_state", "expected_stall", "expected_no_path_out",
        "expected_state_id", "expected_proposed_action", "expected_selected_action",
        "expected_profile_payload_hex", "expected_switched", "expected_dwell_count_sat",
    )
    with rtl_path.open("w", encoding="utf-8", newline="") as handle:
        for row in cycle_rows:
            values = [
                str(int(row[name], 16)) if name == "expected_profile_payload_hex" else str(row[name])
                for name in numeric_columns
            ]
            handle.write(" ".join(values) + "\n")
    with trace_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRACE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(trace_rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycle-csv-out", type=Path, default=DEFAULT_CYCLE_CSV)
    parser.add_argument("--rtl-out", type=Path, default=DEFAULT_RTL)
    parser.add_argument("--trace-csv-out", type=Path, default=DEFAULT_TRACE_CSV)
    args = parser.parse_args()
    rtl_contract = json.loads(RTL_CONTRACT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    policy = tuple(int(line, 16) for line in POLICY_MEM.read_text(encoding="ascii").splitlines())
    profiles = tuple(int(line, 16) for line in PROFILE_MEM.read_text(encoding="ascii").splitlines())
    manual_rows, test_rows, test_seed = frozen_h4_timelines(policy, profiles)
    cycle_rows = build_cycle_vectors(rtl_contract, schema, policy, profiles, manual_rows, test_rows)
    trace_rows = (*manual_rows, *test_rows)
    write_outputs(cycle_rows, trace_rows, schema, args.cycle_csv_out, args.rtl_out, args.trace_csv_out)
    print(f"P4_INTEGRATED_CYCLE_VECTOR_COUNT={len(cycle_rows)}")
    print("P4_INTEGRATED_VALID_DECISIONS=530")
    print(f"P4_INTEGRATED_FROZEN_TRACE_DECISIONS={len(trace_rows)}")
    print("P4_INTEGRATED_FROZEN_TRACE_COUNT=2")
    print(f"P4_INTEGRATED_TEST_SEED={test_seed}")
    print(f"P4_INTEGRATED_MANUAL_TRACE_SHA256={manual_rows[0]['trace_sha256']}")
    print(f"P4_INTEGRATED_TEST_TRACE_SHA256={test_rows[0]['trace_sha256']}")
    print(f"P4_INTEGRATED_CYCLE_CSV_SHA256={sha256(args.cycle_csv_out)}")
    print(f"P4_INTEGRATED_RTL_VECTOR_SHA256={sha256(args.rtl_out)}")
    print(f"P4_INTEGRATED_H4_TIMELINE_SHA256={sha256(args.trace_csv_out)}")


if __name__ == "__main__":
    main()
