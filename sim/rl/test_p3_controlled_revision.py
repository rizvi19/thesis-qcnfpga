"""Tests for the single controlled P3 validation-only dwell revision."""

import json
import unittest

from rl.dwell_controller import MinimumDwellController
from rl.mdp_contract import RewardInput, calculate_reward
from rl.p3_controlled_revision import (
    BALANCE_WEIGHT,
    MINIMUM_DWELL,
    TEST_SEEDS,
    load_revision_config,
)


class TestMinimumDwellController(unittest.TestCase):
    def test_three_decision_dwell_delays_changes_without_altering_policy(self):
        policy = [0] * 256
        policy[1] = 1
        controller = MinimumDwellController(policy, 3)
        actions = [controller.choose_action(state_id) for state_id in (0, 1, 1, 1, 0, 0, 0)]
        self.assertEqual(actions, [0, 0, 0, 1, 1, 1, 0])
        self.assertEqual(policy[1], 1)

    def test_reset_removes_cross_trace_history(self):
        policy = [0] * 256
        policy[1] = 1
        controller = MinimumDwellController(policy, 3)
        controller.choose_action(0)
        controller.reset()
        self.assertEqual(controller.choose_action(1), 1)

    def test_invalid_policy_and_dwell_are_rejected(self):
        with self.assertRaises(ValueError):
            MinimumDwellController([0] * 255, 3)
        with self.assertRaises(ValueError):
            MinimumDwellController([0] * 256, 0)


class TestControlledRevisionContract(unittest.TestCase):
    def test_revision_config_preserves_test_lock_and_one_revision(self):
        config = load_revision_config()
        self.assertEqual(MINIMUM_DWELL, 3)
        self.assertEqual(BALANCE_WEIGHT, 4.0)
        self.assertEqual(tuple(config["effective_contract"]["test_seeds"]), TEST_SEEDS)
        self.assertTrue(config["revision_policy"]["test_partition_remains_locked"])
        self.assertFalse(config["revision_policy"]["additional_revision_allowed"])
        self.assertTrue(config["controlled_revision"]["training_reward"]["evaluation_reward_unchanged"])

    def test_switch_reward_depends_on_hidden_previous_profile(self):
        common = dict(success=True, action_id=1, bottleneck_fidelity=0.96, post_decision_imbalance=0.2, selected_path_hops=3)
        same = calculate_reward(RewardInput(previous_action_id=1, **common))
        changed = calculate_reward(RewardInput(previous_action_id=0, **common))
        self.assertAlmostEqual(changed.total - same.total, -0.25)

    def test_revision_has_no_test_evaluation_entry_point(self):
        import rl.p3_controlled_revision as revision
        self.assertFalse(hasattr(revision, "evaluate_test"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
