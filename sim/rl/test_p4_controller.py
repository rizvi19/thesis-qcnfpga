"""Independent P4 Step 6 cycle and structural tests for rl_controller.v."""

import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from rl.dwell_controller import MinimumDwellController


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "rl/config/p4_rtl_contract_v1.json"
SCHEMA_PATH = REPO_ROOT / "sim/rl/p4_golden_vector_schema.json"
POLICY_MEM = REPO_ROOT / "results/rl/p3_export/policy_rom.mem"
PROFILE_MEM = REPO_ROOT / "results/rl/p3_export/profile_rom.mem"
RTL_PATH = REPO_ROOT / "rtl/rl/rl_controller.v"
GENERATOR_PATH = REPO_ROOT / "sim/rl/p4_generate_controller_unit_vectors.py"
CSV_PATH = REPO_ROOT / "sim/rl/p4_controller_unit_vectors.csv"
RTL_VECTOR_PATH = REPO_ROOT / "sim/rl/p4_controller_unit_vectors.txt"


def rows():
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class TestControllerSchemaAndTimeline(unittest.TestCase):
    def test_vectors_use_exact_frozen_golden_schema(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        with CSV_PATH.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(reader.fieldnames, schema["columns"])
            observed = list(reader)
        self.assertEqual(len(observed), 49)
        self.assertEqual([int(row["cycle"]) for row in observed], list(range(49)))
        self.assertEqual(len({row["case_id"] for row in observed}), 49)

    def test_every_valid_acceptance_completes_exactly_three_cycles_later(self):
        observed = rows()
        accept_categories = {"valid_accept", "back_to_back_requests"}
        accept_cycles = [int(row["cycle"]) for row in observed if row["category"] in accept_categories]
        self.assertEqual(len(accept_cycles), 11)
        for cycle in accept_cycles:
            self.assertEqual(observed[cycle]["expected_busy"], "1")
            self.assertEqual(observed[cycle]["expected_done"], "0")
            self.assertEqual(observed[cycle + 1]["expected_busy"], "1")
            self.assertEqual(observed[cycle + 2]["expected_busy"], "1")
            self.assertEqual(observed[cycle + 3]["expected_busy"], "0")
            self.assertEqual(observed[cycle + 3]["expected_done"], "1")
            self.assertEqual(observed[cycle + 3]["expected_output_valid"], "1")

    def test_reset_is_dominant_and_clears_published_and_dwell_state(self):
        reset_rows = [row for row in rows() if row["category"] == "reset"]
        self.assertEqual(len(reset_rows), 2)
        for row in reset_rows:
            self.assertEqual(row["rst"], "1")
            self.assertEqual(row["start"], "1")
            self.assertEqual(row["expected_ready"], "1")
            for name in (
                "expected_busy", "expected_done", "expected_output_valid", "expected_invalid_state",
                "expected_stall", "expected_no_path_out", "expected_state_id",
                "expected_proposed_action", "expected_selected_action", "expected_switched",
                "expected_dwell_count_sat",
            ):
                self.assertEqual(row[name], "0")
            self.assertEqual(row["expected_profile_payload_hex"], "00000")

    def test_invalid_request_completes_without_changing_decision_or_dwell(self):
        observed = rows()
        index = next(i for i, row in enumerate(observed) if row["category"] == "invalid_input")
        request = observed[index]
        row = observed[index + 1]
        self.assertEqual(request["expected_ready"], "0")
        self.assertEqual(request["expected_busy"], "1")
        self.assertEqual(request["expected_done"], "0")
        self.assertEqual(row["category"], "invalid_complete")
        self.assertEqual(row["expected_ready"], "1")
        self.assertEqual(row["expected_done"], "1")
        self.assertEqual(row["expected_invalid_state"], "1")
        self.assertEqual(row["expected_output_valid"], "0")
        for field in ("expected_state_id", "expected_proposed_action", "expected_selected_action",
                      "expected_profile_payload_hex", "expected_dwell_count_sat"):
            self.assertEqual(request[field], observed[index - 1][field])
            self.assertEqual(row[field], observed[index - 1][field])

    def test_start_while_busy_stalls_without_altering_active_transaction(self):
        observed = rows()
        stalls = [row for row in observed if row["category"] == "start_while_busy"]
        self.assertEqual(len(stalls), 1)
        row = stalls[0]
        self.assertEqual(row["start"], "1")
        self.assertEqual(row["expected_busy"], "1")
        self.assertEqual(row["expected_stall"], "1")
        self.assertEqual(row["expected_done"], "0")
        self.assertEqual(row["expected_output_valid"], "0")

    def test_no_path_is_reported_with_valid_completion_and_advances_dwell(self):
        no_path_rows = [row for row in rows() if row["category"] == "no_path_passthrough"]
        self.assertEqual(len(no_path_rows), 1)
        row = no_path_rows[0]
        self.assertEqual(row["expected_done"], "1")
        self.assertEqual(row["expected_output_valid"], "1")
        self.assertEqual(row["expected_no_path_out"], "1")
        self.assertEqual(row["expected_dwell_count_sat"], "2")


class TestDwellAndPayloadEquivalence(unittest.TestCase):
    def test_completion_actions_match_frozen_python_dwell_controller(self):
        policy = tuple(int(line, 16) for line in POLICY_MEM.read_text(encoding="ascii").splitlines())
        controller = MinimumDwellController(policy, 3)
        previous_action = None
        for row in rows():
            if row["rst"] == "1":
                controller.reset()
                previous_action = None
            if row["expected_done"] == "1" and row["expected_output_valid"] == "1":
                state_id = int(row["expected_state_id"])
                selected = controller.choose_action(state_id)
                self.assertEqual(int(row["expected_proposed_action"]), policy[state_id])
                self.assertEqual(int(row["expected_selected_action"]), selected)
                self.assertEqual(int(row["expected_dwell_count_sat"]), min(3, controller.dwell_count))
                expected_switched = int(previous_action is not None and selected != previous_action)
                self.assertEqual(int(row["expected_switched"]), expected_switched)
                previous_action = selected

    def test_every_completed_payload_matches_selected_action_exactly(self):
        profiles = tuple(int(line, 16) for line in PROFILE_MEM.read_text(encoding="ascii").splitlines())
        completions = [row for row in rows() if row["expected_output_valid"] == "1"]
        self.assertEqual(len(completions), 11)
        for row in completions:
            selected = int(row["expected_selected_action"])
            self.assertEqual(int(row["expected_profile_payload_hex"], 16), profiles[selected])

    def test_dwell_hold_and_switch_categories_are_both_exercised(self):
        observed = rows()
        holds = [row for row in observed if row["category"] == "dwell_hold"]
        switches = [row for row in observed if row["category"] == "dwell_switch"]
        self.assertGreaterEqual(len(holds), 3)
        self.assertGreaterEqual(len(switches), 3)
        self.assertTrue(all(row["expected_proposed_action"] != row["expected_selected_action"] for row in holds))
        self.assertTrue(all(row["expected_switched"] == "1" for row in switches))


class TestReproducibilityAndRTL(unittest.TestCase):
    def test_numeric_rtl_vectors_match_csv(self):
        observed = rows()
        numeric = RTL_VECTOR_PATH.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(numeric), len(observed))
        columns = (
            "cycle", "rst", "start", "input_valid", "no_path_in",
            "min_key_occupancy_u16", "bottleneck_fidelity_u16", "offered_request_load_u16",
            "utilization_imbalance_u16", "expected_ready", "expected_busy", "expected_done",
            "expected_output_valid", "expected_invalid_state", "expected_stall", "expected_no_path_out",
            "expected_state_id", "expected_proposed_action", "expected_selected_action",
            "expected_profile_payload_hex", "expected_switched", "expected_dwell_count_sat",
        )
        for row, line in zip(observed, numeric):
            expected = tuple(
                int(row[name], 16) if name == "expected_profile_payload_hex" else int(row[name])
                for name in columns
            )
            self.assertEqual(tuple(map(int, line.split())), expected)

    def test_generator_is_byte_reproducible(self):
        spec = importlib.util.spec_from_file_location("p4_controller_generator", GENERATOR_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        policy = tuple(int(line, 16) for line in POLICY_MEM.read_text(encoding="ascii").splitlines())
        profiles = tuple(int(line, 16) for line in PROFILE_MEM.read_text(encoding="ascii").splitlines())
        generated = module.build_vectors(contract, schema, policy, profiles)
        with tempfile.TemporaryDirectory() as directory:
            csv_output = Path(directory) / "vectors.csv"
            rtl_output = Path(directory) / "vectors.txt"
            module.write_vectors(generated, schema, csv_output, rtl_output)
            self.assertEqual(csv_output.read_bytes(), CSV_PATH.read_bytes())
            self.assertEqual(rtl_output.read_bytes(), RTL_VECTOR_PATH.read_bytes())

    def test_rtl_integrates_frozen_modules_with_verilog_2001_controls(self):
        text = RTL_PATH.read_text(encoding="utf-8")
        required = (
            "module rl_controller", "rl_state_encoder state_encoder_i", "rl_policy_rom policy_rom_i",
            "rl_profile_rom profile_rom_i", "always @(posedge clk)", "assign ready =",
            "assign busy  =", "current_action_valid", "current_dwell_count >= 2'd3",
            "dwell_next_count", "STATE_WAIT_POLICY", "STATE_WAIT_PROFILE",
            "STATE_INVALID", "if ((controller_state != STATE_IDLE) && start)", "if (input_valid)",
        )
        for token in required:
            self.assertIn(token, text)
        for forbidden in ("always_ff", "always_comb", "logic ", "typedef", "package ", "interface "):
            self.assertNotIn(forbidden, text)
        self.assertNotIn("q_update", text)
        self.assertNotIn("rl_argmax", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
