#!/usr/bin/env python3
"""Generate cycle-exact P4 Step 6 controller unit vectors."""

import argparse
import csv
import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "rl/config/p4_rtl_contract_v1.json"
SCHEMA_PATH = REPO_ROOT / "sim/rl/p4_golden_vector_schema.json"
POLICY_MEM = REPO_ROOT / "results/rl/p3_export/policy_rom.mem"
PROFILE_MEM = REPO_ROOT / "results/rl/p3_export/profile_rom.mem"
DEFAULT_CSV = REPO_ROOT / "sim/rl/p4_controller_unit_vectors.csv"
DEFAULT_RTL = REPO_ROOT / "sim/rl/p4_controller_unit_vectors.txt"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoded_bin(value, thresholds):
    return sum(value >= threshold for threshold in thresholds)


class ControllerModel:
    def __init__(self, contract, policy, profiles):
        self.contract = contract
        self.policy = policy
        self.profiles = profiles
        state = contract["state_interface"]
        self.feature_order = tuple(state["feature_order_msb_to_lsb"])
        self.thresholds = {
            name: tuple(state["features"][name]["threshold_codes"])
            for name in self.feature_order
        }
        self.reset()

    def reset(self):
        self.remaining = 0
        self.pending = None
        self.current_valid = False
        self.current_action = 0
        self.current_dwell = 0
        self.state_id = 0
        self.proposed_action = 0
        self.selected_action = 0
        self.profile_payload = 0
        self.dwell_count = 0

    def encode(self, values):
        state_id = 0
        for name, value in zip(self.feature_order, values):
            state_id = state_id * 4 + encoded_bin(value, self.thresholds[name])
        return state_id

    def choose(self, proposed):
        if not self.current_valid:
            selected, count, switched = proposed, 1, 0
        elif proposed != self.current_action and self.current_dwell >= 3:
            selected, count, switched = proposed, 1, 1
        else:
            selected = self.current_action
            count = min(3, self.current_dwell + 1)
            switched = 0
        self.current_valid = True
        self.current_action = selected
        self.current_dwell = count
        return selected, count, switched

    def step(self, inputs):
        if inputs["rst"]:
            self.reset()
            return self.outputs(done=0, output_valid=0, invalid=0, stall=0, no_path=0, switched=0)

        pre_busy = self.remaining > 0
        done = output_valid = invalid = stall = no_path = switched = 0
        if pre_busy and inputs["start"]:
            stall = 1

        if pre_busy:
            self.remaining -= 1
            if self.remaining == 0:
                pending = self.pending
                done = 1
                if pending["kind"] == "invalid":
                    invalid = 1
                else:
                    self.state_id = pending["state_id"]
                    self.proposed_action = pending["proposed_action"]
                    self.selected_action = pending["selected_action"]
                    self.profile_payload = pending["profile_payload"]
                    self.dwell_count = pending["dwell_count"]
                    output_valid = 1
                    no_path = pending["no_path"]
                    switched = pending["switched"]
                self.pending = None
        elif inputs["start"]:
            if not inputs["input_valid"]:
                self.pending = {"kind": "invalid"}
                self.remaining = 1
            else:
                values = (
                    inputs["min_key_occupancy_u16"],
                    inputs["bottleneck_fidelity_u16"],
                    inputs["offered_request_load_u16"],
                    inputs["utilization_imbalance_u16"],
                )
                state_id = self.encode(values)
                proposed = self.policy[state_id]
                selected, count, did_switch = self.choose(proposed)
                self.pending = {
                    "kind": "valid",
                    "state_id": state_id,
                    "proposed_action": proposed,
                    "selected_action": selected,
                    "profile_payload": self.profiles[selected],
                    "dwell_count": count,
                    "no_path": inputs["no_path_in"],
                    "switched": did_switch,
                }
                self.remaining = 3

        return self.outputs(done, output_valid, invalid, stall, no_path, switched)

    def outputs(self, done, output_valid, invalid, stall, no_path, switched):
        return {
            "expected_ready": int(self.remaining == 0),
            "expected_busy": int(self.remaining != 0),
            "expected_done": done,
            "expected_output_valid": output_valid,
            "expected_invalid_state": invalid,
            "expected_stall": stall,
            "expected_no_path_out": no_path,
            "expected_state_id": self.state_id,
            "expected_proposed_action": self.proposed_action,
            "expected_selected_action": self.selected_action,
            "expected_profile_payload_hex": f"{self.profile_payload:05X}",
            "expected_switched": switched,
            "expected_dwell_count_sat": self.dwell_count,
        }


def build_vectors(contract, schema, policy, profiles):
    model = ControllerModel(contract, policy, profiles)
    state = contract["state_interface"]
    thresholds = {
        name: tuple(state["features"][name]["threshold_codes"])
        for name in model.feature_order
    }
    representatives = {name: (0, *thresholds[name]) for name in model.feature_order}
    states_by_action = {}
    for state_id, action in enumerate(policy):
        states_by_action.setdefault(action, state_id)
    if set(states_by_action) != {0, 1, 2, 3}:
        raise RuntimeError("policy does not expose all four actions")

    def inputs_for_action(action):
        state_id = states_by_action[action]
        bins = ((state_id >> 6) & 3, (state_id >> 4) & 3, (state_id >> 2) & 3, state_id & 3)
        values = tuple(representatives[name][bin_index] for name, bin_index in zip(model.feature_order, bins))
        if model.encode(values) != state_id:
            raise RuntimeError("representative state encoding mismatch")
        return values

    rows = []
    zero_values = (0, 0, 0, 0)

    def append(category, rst=0, start=0, input_valid=1, no_path=0, values=zero_values, notes=""):
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
            "case_id": f"ctrl_{len(rows):03d}",
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

    append("reset", rst=1, start=1, notes="synchronous reset dominates start")
    append("idle", input_valid=0, notes="idle ready state")

    previous_was_completion = False

    def transaction(action, no_path=False, inject_stall=False):
        nonlocal previous_was_completion
        values = inputs_for_action(action)
        category = "back_to_back_requests" if previous_was_completion else "valid_accept"
        append(category, start=1, input_valid=1, no_path=int(no_path), values=values,
               notes=f"accept policy proposal action {action}")
        if inject_stall:
            append("start_while_busy", start=1, input_valid=1, values=inputs_for_action((action + 1) % 4),
                   notes="busy start rejected without changing active transaction")
        else:
            append("pipeline_wait", notes="registered pipeline wait 1")
        append("pipeline_wait", notes="registered pipeline wait 2")
        append("auto_complete", notes="valid completion after three-cycle latency")
        previous_was_completion = True

    transaction(0)
    transaction(1, inject_stall=True)
    transaction(1)
    transaction(1)
    transaction(1)
    append("invalid_input", start=1, input_valid=0, notes="invalid request completes without dwell update")
    append("invalid_complete", notes="invalid status after frozen one-cycle response latency")
    previous_was_completion = False
    transaction(2)
    transaction(2)
    transaction(2, no_path=True)
    transaction(3)
    transaction(3)
    append("reset", rst=1, start=1, notes="reset clears action and dwell history")
    previous_was_completion = False
    transaction(2)

    if tuple(schema["columns"]) != tuple(rows[0].keys()):
        raise RuntimeError("controller unit vectors do not use the frozen golden schema columns")
    return rows


def write_vectors(rows, schema, csv_path, rtl_path):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    rtl_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=schema["columns"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
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
            values = []
            for column in numeric_columns:
                value = row[column]
                values.append(str(int(value, 16)) if column == "expected_profile_payload_hex" else str(value))
            handle.write(" ".join(values) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--rtl-out", type=Path, default=DEFAULT_RTL)
    args = parser.parse_args()
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    policy = tuple(int(line, 16) for line in POLICY_MEM.read_text(encoding="ascii").splitlines())
    profiles = tuple(int(line, 16) for line in PROFILE_MEM.read_text(encoding="ascii").splitlines())
    rows = build_vectors(contract, schema, policy, profiles)
    write_vectors(rows, schema, args.csv_out, args.rtl_out)
    categories = sorted({row["category"] for row in rows})
    print(f"P4_CONTROLLER_UNIT_VECTOR_COUNT={len(rows)}")
    print(f"P4_CONTROLLER_UNIT_CATEGORIES={json.dumps(categories, separators=(',', ':'))}")
    print(f"P4_CONTROLLER_UNIT_CSV_SHA256={sha256(args.csv_out)}")
    print(f"P4_CONTROLLER_UNIT_RTL_VECTOR_SHA256={sha256(args.rtl_out)}")


if __name__ == "__main__":
    main()
