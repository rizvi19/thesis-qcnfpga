"""Independent P4 Step 7 frozen-trace and integrated-cycle tests."""

import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from rl.dwell_controller import MinimumDwellController
from rl.mdp_contract import CONTRACT as MDP_CONTRACT


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = REPO_ROOT / "sim/rl/p4_generate_integrated_trace_vectors.py"
CYCLE_CSV = REPO_ROOT / "sim/rl/p4_integrated_trace_vectors.csv"
RTL_VECTORS = REPO_ROOT / "sim/rl/p4_integrated_trace_vectors.txt"
TRACE_CSV = REPO_ROOT / "sim/rl/p4_h4_frozen_trace_timeline.csv"
SCHEMA_PATH = REPO_ROOT / "sim/rl/p4_golden_vector_schema.json"
TRACE_MANIFEST_PATH = REPO_ROOT / "results/rl/p2_environment/trace_manifest.json"
POLICY_MEM = REPO_ROOT / "results/rl/p3_export/policy_rom.mem"
PROFILE_MEM = REPO_ROOT / "results/rl/p3_export/profile_rom.mem"
TB_PATH = REPO_ROOT / "sim/rl/tb_rl_controller_integrated.v"
STATUS_PATH = REPO_ROOT / "docs/rl/p4_step7_status.md"


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class TestFrozenH4Traces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = read_csv(TRACE_CSV)
        cls.policy = tuple(int(line, 16) for line in POLICY_MEM.read_text(encoding="ascii").splitlines())
        cls.profiles = tuple(int(line, 16) for line in PROFILE_MEM.read_text(encoding="ascii").splitlines())
        cls.manifest = json.loads(TRACE_MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manual_and_locked_test_trace_membership_is_exact(self):
        manual = [row for row in self.rows if row["partition"] == "manual"]
        test = [row for row in self.rows if row["partition"] == "test"]
        self.assertEqual(len(self.rows), 520)
        self.assertEqual(len(manual), 8)
        self.assertEqual(len(test), 512)
        self.assertEqual({row["trace_id"] for row in manual}, {"manual_ring6_v0"})
        self.assertEqual({int(row["seed"]) for row in test}, {int(MDP_CONTRACT["partitions"]["test_seeds"][0])})

    def test_trace_hashes_match_the_frozen_p2_manifest(self):
        manual_hash = self.manifest["manual_trace"]["trace_sha256"]
        test_seed = int(MDP_CONTRACT["partitions"]["test_seeds"][0])
        test_hash = next(
            item["sha256"] for item in self.manifest["traces"]
            if item["partition"] == "test" and int(item["seed"]) == test_seed
        )
        self.assertEqual({row["trace_sha256"] for row in self.rows if row["partition"] == "manual"}, {manual_hash})
        self.assertEqual({row["trace_sha256"] for row in self.rows if row["partition"] == "test"}, {test_hash})

    def test_action_and_dwell_timelines_match_frozen_python_controller(self):
        for partition in ("manual", "test"):
            controller = MinimumDwellController(self.policy, 3)
            previous = None
            partition_rows = [row for row in self.rows if row["partition"] == partition]
            for row in partition_rows:
                state_id = int(row["state_id"])
                selected = controller.choose_action(state_id)
                self.assertEqual(int(row["proposed_action"]), self.policy[state_id])
                self.assertEqual(int(row["selected_action"]), selected)
                self.assertEqual(int(row["dwell_count_sat"]), min(3, controller.dwell_count))
                self.assertEqual(int(row["switched"]), int(previous is not None and selected != previous))
                previous = selected

    def test_every_frozen_trace_profile_payload_is_exact(self):
        for row in self.rows:
            selected = int(row["selected_action"])
            self.assertEqual(int(row["profile_payload_hex"], 16), self.profiles[selected])
            self.assertEqual(int(row["no_path"]), 1 - int(row["success"]))

    def test_each_independent_trace_has_one_final_done(self):
        for partition, length in (("manual", 8), ("test", 512)):
            rows = [row for row in self.rows if row["partition"] == partition]
            self.assertEqual([int(row["trace_index"]) for row in rows], list(range(length)))
            self.assertEqual(sum(int(row["done"]) for row in rows), 1)
            self.assertEqual(rows[-1]["done"], "1")


class TestIntegratedCycleTimeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = read_csv(CYCLE_CSV)

    def test_exact_schema_cycle_count_and_case_identity(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        with CYCLE_CSV.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(reader.fieldnames, schema["columns"])
        self.assertEqual(len(self.rows), 2125)
        self.assertEqual([int(row["cycle"]) for row in self.rows], list(range(2125)))
        self.assertEqual(len({row["case_id"] for row in self.rows}), 2125)

    def test_all_530_valid_acceptances_complete_after_n_plus_3(self):
        accepts = [
            int(row["cycle"]) for row in self.rows
            if row["category"] in {"valid_accept", "back_to_back_requests"}
        ]
        self.assertEqual(len(accepts), 530)
        for cycle in accepts:
            self.assertEqual(self.rows[cycle]["expected_busy"], "1")
            self.assertEqual(self.rows[cycle + 3]["expected_ready"], "1")
            self.assertEqual(self.rows[cycle + 3]["expected_done"], "1")
            self.assertEqual(self.rows[cycle + 3]["expected_output_valid"], "1")

    def test_reset_invalid_stall_and_back_to_back_rules_are_explicit(self):
        categories = [row["category"] for row in self.rows]
        self.assertEqual(categories.count("reset"), 3)
        self.assertEqual(categories.count("invalid_input"), 1)
        self.assertEqual(categories.count("invalid_complete"), 1)
        self.assertEqual(categories.count("start_while_busy"), 2)
        self.assertEqual(categories.count("back_to_back_requests"), 527)
        invalid = categories.index("invalid_input")
        self.assertEqual(self.rows[invalid]["expected_done"], "0")
        self.assertEqual(self.rows[invalid + 1]["expected_done"], "1")
        self.assertEqual(self.rows[invalid + 1]["expected_invalid_state"], "1")

    def test_profile_changes_dwell_no_path_and_all_actions_are_covered(self):
        completions = [row for row in self.rows if row["expected_output_valid"] == "1"]
        self.assertEqual(len(completions), 530)
        self.assertEqual({int(row["expected_selected_action"]) for row in completions}, {0, 1, 2, 3})
        self.assertTrue(any(row["category"] == "dwell_hold" for row in completions))
        self.assertTrue(any(row["category"] == "dwell_switch" for row in completions))
        self.assertTrue(any(row["category"] == "no_path_passthrough" for row in completions))
        self.assertTrue(all(1 <= int(row["expected_dwell_count_sat"]) <= 3 for row in completions))

    def test_published_outputs_hold_between_valid_completions(self):
        published = (
            "expected_state_id", "expected_proposed_action", "expected_selected_action",
            "expected_profile_payload_hex", "expected_dwell_count_sat",
        )
        previous = {name: "0" if name != "expected_profile_payload_hex" else "00000" for name in published}
        for row in self.rows:
            if row["rst"] == "1":
                previous = {name: "0" if name != "expected_profile_payload_hex" else "00000" for name in published}
            elif row["expected_output_valid"] == "0":
                for name in published:
                    self.assertEqual(row[name], previous[name])
            else:
                previous = {name: row[name] for name in published}


class TestReproducibilityAndBoundary(unittest.TestCase):
    def test_numeric_rtl_vectors_match_cycle_csv(self):
        rows = read_csv(CYCLE_CSV)
        numeric = RTL_VECTORS.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(numeric), len(rows))
        columns = (
            "cycle", "rst", "start", "input_valid", "no_path_in",
            "min_key_occupancy_u16", "bottleneck_fidelity_u16", "offered_request_load_u16",
            "utilization_imbalance_u16", "expected_ready", "expected_busy", "expected_done",
            "expected_output_valid", "expected_invalid_state", "expected_stall", "expected_no_path_out",
            "expected_state_id", "expected_proposed_action", "expected_selected_action",
            "expected_profile_payload_hex", "expected_switched", "expected_dwell_count_sat",
        )
        for row, line in zip(rows, numeric):
            expected = tuple(int(row[name], 16) if name == "expected_profile_payload_hex" else int(row[name]) for name in columns)
            self.assertEqual(tuple(map(int, line.split())), expected)

    def test_generator_is_byte_reproducible(self):
        spec = importlib.util.spec_from_file_location("p4_integrated_generator", GENERATOR_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rtl_contract = json.loads((REPO_ROOT / "rl/config/p4_rtl_contract_v1.json").read_text())
        schema = json.loads(SCHEMA_PATH.read_text())
        policy = tuple(int(line, 16) for line in POLICY_MEM.read_text().splitlines())
        profiles = tuple(int(line, 16) for line in PROFILE_MEM.read_text().splitlines())
        manual, test, _seed = module.frozen_h4_timelines(policy, profiles)
        cycles = module.build_cycle_vectors(rtl_contract, schema, policy, profiles, manual, test)
        with tempfile.TemporaryDirectory() as directory:
            cycle = Path(directory) / "cycle.csv"
            rtl = Path(directory) / "rtl.txt"
            trace = Path(directory) / "trace.csv"
            module.write_outputs(cycles, (*manual, *test), schema, cycle, rtl, trace)
            self.assertEqual(cycle.read_bytes(), CYCLE_CSV.read_bytes())
            self.assertEqual(rtl.read_bytes(), RTL_VECTORS.read_bytes())
            self.assertEqual(trace.read_bytes(), TRACE_CSV.read_bytes())

    def test_step7_boundary_excludes_synthesis_board_and_learning_claims(self):
        status = STATUS_PATH.read_text(encoding="utf-8")
        self.assertRegex(status, r"ISE\s+synthesis")
        for phrase in ("Step 8", "board programming", "EEPROM access", "online", "q_update.v"):
            self.assertIn(phrase, status)
        tb = TB_PATH.read_text(encoding="utf-8")
        self.assertIn("module tb_rl_controller_integrated", tb)
        self.assertIn("P4_INTEGRATED_RTL_PASS", tb)
        self.assertNotIn("force ", tb)
        self.assertNotIn("q_update", tb)


if __name__ == "__main__":
    unittest.main(verbosity=2)
