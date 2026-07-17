"""Tests for the consolidated P2 evidence manifest and exit decision."""

import tempfile
from pathlib import Path
import unittest

from rl.p2_exit_gate import (
    FORBIDDEN_P3_PATHS,
    PRIOR_EVIDENCE_DIRS,
    REPO_ROOT,
    collect_gate_facts,
    evidence_manifest_records,
    verify_checksum_bundle,
    write_exit_gate_evidence,
)


class TestP2ExitGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.facts = collect_gate_facts()

    def test_all_prior_checksum_bundles_pass(self):
        counts = [verify_checksum_bundle(path) for path in PRIOR_EVIDENCE_DIRS]
        self.assertEqual(counts, [3, 1, 3, 4, 3])
        self.assertEqual(sum(counts), 14)

    def test_forced_fixed_gate_facts(self):
        facts = self.facts["forced_fixed"]
        self.assertTrue(facts["canonical_json_byte_identical"])
        self.assertTrue(facts["route_selection_parity"])
        self.assertEqual(facts["forced_balanced_step_count"], 8192)
        self.assertFalse(facts["training_performed"])

    def test_contract_partitions_and_manual_trace_are_frozen(self):
        facts = self.facts["mdp_and_partitions"]
        self.assertEqual(facts["state_count"], 256)
        self.assertEqual(facts["action_count"], 4)
        self.assertEqual(facts["partition_seed_counts"], {"train": 8, "validation": 4, "test": 4})
        self.assertEqual(facts["frozen_trace_count"], 16)
        self.assertEqual(facts["manual_trace_steps"], 8)
        self.assertFalse(facts["dqn_allowed_in_p2"])

    def test_sensitivity_selection_matches_codebook(self):
        facts = self.facts["profile_selection"]
        self.assertEqual(facts["profile_count"], 4)
        self.assertEqual(facts["adaptive_profiles_selected_by_sensitivity"], 3)
        self.assertEqual(facts["scenario_count"], 5)

    def test_hardware_gate_facts(self):
        facts = self.facts["hardware_coefficients"]
        self.assertTrue(facts["p2_hardware_coefficient_gate_passed"])
        self.assertEqual(facts["route_equivalence_matches"], 24)
        self.assertEqual(facts["codebook_rom_payload_bits_total"], 72)
        self.assertEqual(facts["generic_profile_multiplier_budget"], 0)

    def test_manifest_is_sorted_unique_and_complete(self):
        records = evidence_manifest_records()
        paths = [item["path"] for item in records]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(len(paths), len(set(paths)))
        self.assertIn("docs/rl/p2_status.md", paths)
        self.assertIn("docs/rl/p2_exit_gate.md", paths)
        self.assertIn("rl/p2_exit_gate.py", paths)
        self.assertIn("sim/rl/test_p2_exit_gate.py", paths)

    def test_exit_evidence_is_byte_reproducible(self):
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = Path(first_dir)
            second = Path(second_dir)
            summary = write_exit_gate_evidence(
                first, legacy_test_count=26, p2_test_count=72, tests_passed=True, facts=self.facts
            )
            write_exit_gate_evidence(
                second, legacy_test_count=26, p2_test_count=72, tests_passed=True, facts=self.facts
            )
            self.assertEqual(
                {path.name: path.read_bytes() for path in first.iterdir()},
                {path.name: path.read_bytes() for path in second.iterdir()},
            )
            self.assertEqual(summary["status"], "PASS")
            self.assertTrue(summary["checkpoint_commit_pending"])
            self.assertFalse(summary["p3_authorized_before_step10"])

    def test_no_p3_training_or_deployment_artifact_exists(self):
        self.assertEqual([path for path in FORBIDDEN_P3_PATHS if (REPO_ROOT / path).exists()], [])
        scope = self.facts["scope_boundary"]
        self.assertEqual(scope["forbidden_p3_artifacts_present"], [])
        self.assertEqual(scope["rtl_artifacts_present"], [])
        self.assertFalse(scope["training_performed"])
        self.assertFalse(scope["rtl_implemented"])
        self.assertFalse(scope["board_measurement_claimed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
