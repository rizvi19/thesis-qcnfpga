"""Unit and integration checks for the frozen P3 Step 8 analysis."""

import json
from pathlib import Path
import tempfile
import unittest

from rl.mdp_contract import CONTRACT as MDP_CONTRACT, decode_state_id
from rl.p3_statistics_and_gate import (
    FROZEN_POLICY,
    compute_paired_statistics,
    decide_utility_gate,
    exact_two_sided_paired_permutation,
    feature_marginalized_policy,
    holm_adjust,
    paired_bootstrap_ci,
    validate_frozen_inputs,
    write_step8_evidence,
)


def encode_bins(bins):
    state_id = 0
    for value in bins:
        state_id = state_id * 4 + value
    return state_id


class TestFrozenStatistics(unittest.TestCase):
    def test_exact_p_value_and_holm_power_limit(self):
        self.assertEqual(exact_two_sided_paired_permutation((1.0, 2.0, 3.0, 4.0)), 0.125)
        self.assertEqual(holm_adjust((0.125, 0.125)), (0.25, 0.25))

    def test_bootstrap_is_deterministic(self):
        first = paired_bootstrap_ci((0.1, 0.2, 0.3, 0.4), 1000, 32452843)
        second = paired_bootstrap_ci((0.1, 0.2, 0.3, 0.4), 1000, 32452843)
        self.assertEqual(first, second)
        self.assertGreater(first[0], 0.0)

    def test_frozen_comparisons_have_four_wins_but_insufficient_power(self):
        validate_frozen_inputs()
        statistics, per_seed = compute_paired_statistics()
        self.assertEqual(len(statistics), 2)
        self.assertEqual(len(per_seed), 8)
        for item in statistics:
            self.assertEqual(item["h4_wins"], 4)
            self.assertGreater(item["ci_95_low"], 0.0)
            self.assertEqual(item["raw_permutation_p"], 0.125)
            self.assertEqual(item["holm_adjusted_p"], 0.25)
            self.assertFalse(item["statistical_superiority"])


class TestAblationAndGate(unittest.TestCase):
    def test_feature_marginalization_removes_feature_dependence(self):
        policy = json.loads(FROZEN_POLICY.read_text(encoding="utf-8"))
        for feature_index, _ in enumerate(MDP_CONTRACT["state"]["feature_order"]):
            ablated = feature_marginalized_policy(policy, feature_index)
            for state_id in range(256):
                bins = list(decode_state_id(state_id))
                actions = set()
                for value in range(4):
                    varied = list(bins)
                    varied[feature_index] = value
                    actions.add(ablated[encode_bins(varied)])
                self.assertEqual(len(actions), 1)

    def test_utility_gate_passes_without_superiority_overclaim(self):
        statistics, _ = compute_paired_statistics()
        gate = decide_utility_gate(statistics)
        self.assertEqual(gate["decision"], "PASS_DESCRIPTIVE_INSUFFICIENT_POWER")
        self.assertTrue(gate["all_predeclared_utility_checks_pass"])
        self.assertTrue(gate["p4_authorized_by_p3_utility_gate"])
        self.assertFalse(gate["statistical_superiority_claim_allowed"])
        self.assertFalse(gate["policy_or_training_revision_allowed"])

    def test_step8_evidence_is_byte_reproducible(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_path, second_path = Path(first), Path(second)
            first_result = write_step8_evidence(first_path)
            second_result = write_step8_evidence(second_path)
            self.assertEqual(first_result, second_result)
            for name in (
                "paired_statistics.csv", "per_seed_reward_differences.csv",
                "feature_ablation.csv", "reward_term_ablation.csv", "dwell_ablation.csv",
                "utility_gate.json", "analysis_summary.json", "analysis_manifest.json",
                "SHA256SUMS",
            ):
                self.assertEqual((first_path / name).read_bytes(), (second_path / name).read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
