"""Tests for P3 Step 6 validation-only H4 selection."""

import unittest

from rl.h4_evaluator import evaluate_validation_trace, select_validation_candidate, summarize_validation
from rl.h4_trainer import FROZEN_TRAINER_SEEDS, FULL_SPEC, FULL_TRANSITIONS
from rl.trace_generator import generate_trace


def summary(seed, reward=4.7, block=0.0, fidelity=0.96, switch=0.2, secondary=0.1):
    fractions = [1.0 - secondary, secondary, 0.0, 0.0]
    return {
        "trainer_seed": seed,
        "blocking_rate": block,
        "mean_total_reward": reward,
        "mean_success_bottleneck_fidelity": fidelity,
        "mean_balance_utility_success": 0.2,
        "mean_hops_success": 2.9,
        "switch_rate": switch,
        "profile_counts": [int(value * 1000) for value in fractions],
        "profile_fractions": fractions,
        "distinct_profiles": 2,
        "secondary_profile_fraction": secondary,
    }


BASELINES = [
    {"controller": "h2_forced_fixed", "partition": "validation", "blocking_rate": 0.0},
    {"controller": "h3_threshold", "partition": "validation", "blocking_rate": 0.0},
]


class TestValidationEvaluation(unittest.TestCase):
    def test_policy_evaluation_counts_one_frozen_validation_trace(self):
        trace = generate_trace(1009, 16)
        row = evaluate_validation_trace(17, trace, tuple([0] * 256))
        self.assertEqual(row.partition, "validation")
        self.assertEqual(row.environment_seed, 1009)
        self.assertEqual(row.decision_count, 16)
        self.assertEqual(row.profile_0_count, 16)
        self.assertEqual(row.switch_rate, 0.0)

    def test_nonvalidation_seed_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_validation_trace(17, generate_trace(2003, 8), tuple([0] * 256))

    def test_invalid_policy_is_rejected(self):
        trace = generate_trace(1009, 8)
        for policy in ((0,) * 255, (0,) * 255 + (4,)):
            with self.assertRaises(ValueError):
                evaluate_validation_trace(17, trace, policy)


class TestFrozenSelection(unittest.TestCase):
    def test_exact_full_budget_and_candidate_matrix(self):
        self.assertEqual(FROZEN_TRAINER_SEEDS, (17, 29, 43, 71, 113, 167, 229, 283))
        self.assertEqual(FULL_SPEC.epochs, 200)
        self.assertEqual(FULL_SPEC.transitions, 819200)
        self.assertEqual(FULL_TRANSITIONS * len(FROZEN_TRAINER_SEEDS), 6553600)

    def test_ranking_selects_highest_reward_eligible_candidate(self):
        candidates = [summary(seed, reward=4.6 + index / 100) for index, seed in enumerate(FROZEN_TRAINER_SEEDS)]
        result = select_validation_candidate(candidates, BASELINES)
        self.assertEqual(result["decision"], "PASS")
        self.assertEqual(result["selected_trainer_seed"], 283)
        self.assertEqual(result["eligible_candidate_count"], 8)
        self.assertFalse(result["revision_invoked"])
        self.assertEqual(result["test_access_count"], 0)

    def test_every_frozen_eligibility_gate_is_enforced(self):
        candidates = [summary(seed) for seed in FROZEN_TRAINER_SEEDS]
        candidates[0]["blocking_rate"] = 0.006
        candidates[1]["switch_rate"] = 0.251
        candidates[2]["distinct_profiles"] = 1
        candidates[3]["secondary_profile_fraction"] = 0.009
        result = select_validation_candidate(candidates, BASELINES)
        by_seed = {item["trainer_seed"]: item for item in result["candidate_evaluations"]}
        self.assertIn("blocking_noninferiority", by_seed[17]["ineligibility_reasons"])
        self.assertIn("switch_rate_ceiling", by_seed[29]["ineligibility_reasons"])
        self.assertIn("minimum_distinct_profiles", by_seed[43]["ineligibility_reasons"])
        self.assertIn("minimum_secondary_profile_fraction", by_seed[71]["ineligibility_reasons"])

    def test_no_eligible_candidate_requires_revision_without_test_unlock(self):
        candidates = [summary(seed, switch=0.3) for seed in FROZEN_TRAINER_SEEDS]
        result = select_validation_candidate(candidates, BASELINES)
        self.assertEqual(result["decision"], "REVISION_REQUIRED")
        self.assertIsNone(result["selected_trainer_seed"])
        self.assertTrue(result["revision_invoked"])
        self.assertTrue(result["test_partition_locked"])
        self.assertFalse(result["policy_freeze_performed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
