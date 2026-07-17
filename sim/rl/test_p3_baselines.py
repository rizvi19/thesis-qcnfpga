"""Tests for deterministic H2/H3 P3 baseline evaluation."""

import tempfile
from pathlib import Path
import unittest

from rl.baseline_controllers import H2_ID, H3_ID, action_for, h2_action
from rl.policy_evaluator import evaluate_baselines, evaluate_trace, write_baseline_evidence
from rl.trace_generator import generate_trace


class TestBaselineControllers(unittest.TestCase):
    def test_h2_is_forced_balanced_for_every_state(self):
        self.assertEqual({h2_action(state_id) for state_id in range(256)}, {0})

    def test_h3_is_deterministic_and_uses_all_profiles(self):
        first = [action_for(H3_ID, state_id) for state_id in range(256)]
        second = [action_for(H3_ID, state_id) for state_id in range(256)]
        self.assertEqual(first, second)
        self.assertEqual(set(first), {0, 1, 2, 3})

    def test_unknown_controller_is_rejected(self):
        with self.assertRaises(ValueError):
            action_for("h9_unknown", 0)


class TestBaselineEvaluation(unittest.TestCase):
    def test_locked_test_partition_is_rejected(self):
        trace = generate_trace(2003, 8)
        with self.assertRaises(ValueError):
            evaluate_trace(H2_ID, "test", trace)

    def test_h2_trace_uses_only_profile_zero(self):
        metrics = evaluate_trace(H2_ID, "train", generate_trace(101, 64))
        self.assertEqual(metrics.decision_count, 64)
        self.assertEqual(metrics.profile_0_count, 64)
        self.assertEqual(metrics.profile_1_count + metrics.profile_2_count + metrics.profile_3_count, 0)
        self.assertEqual(metrics.switch_count, 0)
        self.assertEqual(metrics.switch_rate, 0.0)

    def test_metrics_are_bounded(self):
        metrics = evaluate_trace(H3_ID, "validation", generate_trace(1009, 64))
        self.assertTrue(0.0 <= metrics.blocking_rate <= 1.0)
        self.assertTrue(0.0 <= metrics.switch_rate <= 1.0)
        self.assertEqual(metrics.success_count + round(metrics.blocking_rate * metrics.decision_count), metrics.decision_count)
        if metrics.success_count:
            self.assertTrue(0.9 <= metrics.mean_success_bottleneck_fidelity <= 1.0)
            self.assertTrue(0.0 <= metrics.mean_balance_utility_success <= 1.0)
            self.assertGreaterEqual(metrics.mean_hops_success, 1.0)

    def test_full_matrix_has_24_controller_trace_runs(self):
        rows = evaluate_baselines()
        self.assertEqual(len(rows), 24)
        self.assertEqual({row.partition for row in rows}, {"train", "validation"})
        self.assertNotIn(2003, {row.seed for row in rows})

    def test_evidence_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            write_baseline_evidence(Path(first_dir))
            write_baseline_evidence(Path(second_dir))
            names = (
                "baseline_per_seed.csv",
                "baseline_summary.json",
                "profile_usage.csv",
                "evaluation_manifest.json",
                "SHA256SUMS",
            )
            for name in names:
                self.assertEqual((Path(first_dir) / name).read_bytes(), (Path(second_dir) / name).read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
