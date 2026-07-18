"""Independent P4 Step 8 exhaustive, lint-boundary and reproducibility tests."""

import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "rl/config/p4_rtl_contract_v1.json"
SCHEMA_PATH = REPO_ROOT / "sim/rl/p4_golden_vector_schema.json"
POLICY_MEM = REPO_ROOT / "results/rl/p3_export/policy_rom.mem"
PROFILE_MEM = REPO_ROOT / "results/rl/p3_export/profile_rom.mem"
CSV_PATH = REPO_ROOT / "sim/rl/p4_exhaustive_vectors.csv"
RTL_VECTOR_PATH = REPO_ROOT / "sim/rl/p4_exhaustive_vectors.txt"
SUMMARY_PATH = REPO_ROOT / "sim/rl/p4_exhaustive_summary.json"
GENERATOR_PATH = REPO_ROOT / "sim/rl/p4_generate_exhaustive_vectors.py"
STATUS_PATH = REPO_ROOT / "docs/rl/p4_step8_status.md"
DEPLOYMENT_DECISION = REPO_ROOT / "docs/rl/p4_policy_rom_deployment_decision.md"
RTL_PATHS = tuple(REPO_ROOT / f"rtl/rl/{name}" for name in (
    "rl_state_encoder.v", "rl_policy_rom.v", "rl_profile_rom.v", "rl_controller.v"
))


def rows():
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class TestAllStatesAndProfiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = rows()
        cls.policy = tuple(int(line, 16) for line in POLICY_MEM.read_text().splitlines())
        cls.profiles = tuple(int(line, 16) for line in PROFILE_MEM.read_text().splitlines())
        cls.state_rows = [row for row in cls.rows if row["category"] == "all_256_states"]

    def test_exactly_one_isolated_case_exists_for_every_state(self):
        self.assertEqual(len(self.state_rows), 256)
        self.assertEqual([int(row["expected_state_id"]) for row in self.state_rows], list(range(256)))

    def test_every_state_has_exact_frozen_policy_action(self):
        for state_id, row in enumerate(self.state_rows):
            action = self.policy[state_id]
            self.assertEqual(int(row["expected_proposed_action"]), action)
            self.assertEqual(int(row["expected_selected_action"]), action)
            self.assertEqual(row["expected_switched"], "0")
            self.assertEqual(row["expected_dwell_count_sat"], "1")

    def test_every_state_has_exact_selected_profile_payload(self):
        for row in self.state_rows:
            action = int(row["expected_selected_action"])
            self.assertEqual(int(row["expected_profile_payload_hex"], 16), self.profiles[action])

    def test_policy_distribution_and_all_actions_are_preserved(self):
        self.assertEqual([self.policy.count(action) for action in range(4)], [145, 43, 44, 24])
        self.assertEqual({int(row["expected_selected_action"]) for row in self.state_rows}, {0, 1, 2, 3})


class TestThresholdsEndpointsAndExceptions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = rows()
        cls.contract = json.loads(CONTRACT_PATH.read_text())

    def test_all_36_threshold_edges_are_explicit(self):
        edges = [row for row in self.rows if row["category"] in {"threshold_below", "threshold_equal", "threshold_above"}]
        self.assertEqual(len(edges), 36)
        self.assertEqual(sum(row["category"] == "threshold_below" for row in edges), 12)
        self.assertEqual(sum(row["category"] == "threshold_equal" for row in edges), 12)
        self.assertEqual(sum(row["category"] == "threshold_above" for row in edges), 12)

    def test_threshold_equality_enters_the_higher_bin(self):
        equality = [row for row in self.rows if row["category"] == "threshold_equal"]
        feature_names = self.contract["state_interface"]["feature_order_msb_to_lsb"]
        for row in equality:
            note = row["notes"]
            feature_index = next(i for i, name in enumerate(feature_names) if name in note)
            threshold_index = int(note.split("threshold ", 1)[1].split()[0])
            expected_bin = threshold_index + 1
            state_id = int(row["expected_state_id"])
            bins = ((state_id >> 6) & 3, (state_id >> 4) & 3, (state_id >> 2) & 3, state_id & 3)
            self.assertEqual(bins[feature_index], expected_bin)

    def test_below_and_above_codes_straddle_each_threshold_exactly(self):
        state = self.contract["state_interface"]
        for feature_index, feature_name in enumerate(state["feature_order_msb_to_lsb"]):
            input_name = f"{feature_name}_u16"
            for threshold_index, threshold in enumerate(state["features"][feature_name]["threshold_codes"]):
                key = f"{feature_name} threshold {threshold_index}"
                cases = [row for row in self.rows if key in row["notes"] and row["category"].startswith("threshold_")]
                values = {
                    row["category"]: int(self.rows[int(row["cycle"]) - 3][input_name])
                    for row in cases
                }
                self.assertEqual(values, {"threshold_below": threshold - 1, "threshold_equal": threshold, "threshold_above": threshold + 1})

    def test_encoded_endpoints_and_isolated_action_cases_are_explicit(self):
        low = next(row for row in self.rows if row["category"] == "encoded_clip_low")
        high = next(row for row in self.rows if row["category"] == "encoded_clip_high")
        self.assertEqual(int(low["expected_state_id"]), 0)
        self.assertEqual(int(high["expected_state_id"]), 255)
        actions = [row for row in self.rows if row["category"] == "all_four_actions"]
        self.assertEqual({int(row["expected_selected_action"]) for row in actions}, {0, 1, 2, 3})

    def test_exception_dwell_and_handshake_categories_are_all_present(self):
        categories = {row["category"] for row in self.rows}
        required = {"reset", "invalid_input", "invalid_complete", "start_while_busy", "back_to_back_requests", "no_path_passthrough", "dwell_hold", "dwell_switch"}
        self.assertTrue(required.issubset(categories))
        invalid = next(i for i, row in enumerate(self.rows) if row["category"] == "invalid_input")
        self.assertEqual(self.rows[invalid]["expected_done"], "0")
        self.assertEqual(self.rows[invalid + 1]["expected_done"], "1")
        self.assertEqual(self.rows[invalid + 1]["expected_invalid_state"], "1")


class TestCycleReproducibilityAndLintBoundary(unittest.TestCase):
    def test_schema_cycle_count_and_all_n_plus_3_completions_are_exact(self):
        observed = rows()
        schema = json.loads(SCHEMA_PATH.read_text())
        with CSV_PATH.open(encoding="utf-8", newline="") as handle:
            self.assertEqual(csv.DictReader(handle).fieldnames, schema["columns"])
        self.assertEqual(len(observed), 1509)
        accepts = [int(row["cycle"]) for row in observed if row["category"] in {"valid_accept", "back_to_back_requests"}]
        self.assertEqual(len(accepts), 302)
        for cycle in accepts:
            self.assertEqual(observed[cycle + 3]["expected_done"], "1")
            self.assertEqual(observed[cycle + 3]["expected_output_valid"], "1")

    def test_numeric_vectors_match_reviewable_csv(self):
        observed = rows(); numeric = RTL_VECTOR_PATH.read_text().splitlines()
        self.assertEqual(len(numeric), 1509)
        columns = (
            "cycle", "rst", "start", "input_valid", "no_path_in", "min_key_occupancy_u16",
            "bottleneck_fidelity_u16", "offered_request_load_u16", "utilization_imbalance_u16",
            "expected_ready", "expected_busy", "expected_done", "expected_output_valid",
            "expected_invalid_state", "expected_stall", "expected_no_path_out", "expected_state_id",
            "expected_proposed_action", "expected_selected_action", "expected_profile_payload_hex",
            "expected_switched", "expected_dwell_count_sat",
        )
        for row, line in zip(observed, numeric):
            expected = tuple(int(row[name], 16) if name == "expected_profile_payload_hex" else int(row[name]) for name in columns)
            self.assertEqual(tuple(map(int, line.split())), expected)

    def test_generator_is_byte_reproducible(self):
        spec = importlib.util.spec_from_file_location("p4_exhaustive_generator", GENERATOR_PATH)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        contract=json.loads(CONTRACT_PATH.read_text()); schema=json.loads(SCHEMA_PATH.read_text())
        policy=tuple(int(line,16) for line in POLICY_MEM.read_text().splitlines())
        profiles=tuple(int(line,16) for line in PROFILE_MEM.read_text().splitlines())
        generated=module.build_vectors(contract,schema,policy,profiles)
        with tempfile.TemporaryDirectory() as directory:
            csv_out=Path(directory)/"v.csv"; rtl_out=Path(directory)/"v.txt"; summary_out=Path(directory)/"s.json"
            module.write_outputs(generated,schema,policy,profiles,csv_out,rtl_out,summary_out)
            self.assertEqual(csv_out.read_bytes(),CSV_PATH.read_bytes())
            self.assertEqual(rtl_out.read_bytes(),RTL_VECTOR_PATH.read_bytes())
            self.assertEqual(summary_out.read_bytes(),SUMMARY_PATH.read_bytes())

    def test_summary_and_policy_rom_decision_firewall_are_exact(self):
        summary=json.loads(SUMMARY_PATH.read_text())
        expected={
            "cycle_vector_count":1509,"valid_decision_count":302,"all_state_case_count":256,
            "threshold_edge_case_count":36,"encoded_endpoint_case_count":2,"isolated_action_case_count":4,
            "state_action_mismatch_count":0,"state_profile_mismatch_count":0,"unexplained_mismatch_count":0,
            "policy_rom_deployed":True,"q_table_role":"audit_only","runtime_argmax_deployed":False,
            "q_update_implemented":False,"ise_synthesis_performed":False,"board_programming_performed":False,
            "eeprom_access_performed":False,
        }
        for key,value in expected.items(): self.assertEqual(summary[key],value)
        decision=DEPLOYMENT_DECISION.read_text()
        self.assertIn("deploys `policy_rom.mem`",decision)
        self.assertIn("runtime Q-table",decision)
        self.assertIn("audit",decision)

    def test_all_rtl_remains_verilog_2001_without_argmax_or_q_update(self):
        forbidden=("always_ff","always_comb","logic ","typedef","package ","interface ")
        for path in RTL_PATHS:
            text=path.read_text()
            for token in forbidden: self.assertNotIn(token,text)
        self.assertFalse((REPO_ROOT/"rtl/rl/rl_argmax.v").exists())
        self.assertFalse((REPO_ROOT/"rtl/rl/q_update.v").exists())
        status=STATUS_PATH.read_text()
        for phrase in ("audit-only","Verilog-2001","not ISE synthesis","Step 9"):
            self.assertIn(phrase,status)


if __name__ == "__main__":
    unittest.main(verbosity=2)
