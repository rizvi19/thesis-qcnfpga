"""Tests for the pre-training P3 experiment and test-lock contract."""

import unittest

from rl.p3_contract import CONTRACT, h3_action, validate_contract
from rl.mdp_contract import decode_state_id


def state_id(key_bin, fidelity_bin, load_bin, imbalance_bin):
    return (((key_bin * 4) + fidelity_bin) * 4 + load_bin) * 4 + imbalance_bin


class TestP3Contract(unittest.TestCase):
    def test_validation_passes(self):
        summary = validate_contract()
        self.assertEqual(summary["decision"], "PASS")
        self.assertTrue(summary["test_partition_locked"])
        self.assertFalse(summary["h4_training_performed"])

    def test_h3_priority_and_default(self):
        self.assertEqual(h3_action(state_id(0, 0, 3, 3)), 1)
        self.assertEqual(h3_action(state_id(3, 1, 3, 3)), 2)
        self.assertEqual(h3_action(state_id(3, 3, 2, 2)), 1)
        self.assertEqual(h3_action(state_id(2, 2, 3, 1)), 3)
        self.assertEqual(h3_action(state_id(2, 2, 2, 1)), 0)

    def test_h3_is_total_and_uses_all_profiles(self):
        actions = [h3_action(value) for value in range(256)]
        self.assertEqual(set(actions), {0, 1, 2, 3})
        self.assertTrue(all(0 <= action < 4 for action in actions))

    def test_state_bin_order_matches_p2(self):
        self.assertEqual(decode_state_id(state_id(1, 2, 3, 0)), (1, 2, 3, 0))
        self.assertEqual(
            CONTRACT["controller_matrix"]["h3"]["feature_bin_order"],
            [
                "min_key_occupancy",
                "bottleneck_fidelity",
                "offered_request_load",
                "utilization_imbalance",
            ],
        )

    def test_fixed_training_budget(self):
        training = CONTRACT["training"]
        self.assertEqual(training["epochs"], 200)
        self.assertEqual(training["episodes_per_epoch"], 8)
        self.assertEqual(training["transitions_per_trainer"], 819200)
        self.assertFalse(training["early_stopping"]["enabled"])
        self.assertFalse(training["hyperparameter_sweep_allowed"])

    def test_test_partition_is_not_used_for_selection(self):
        self.assertTrue(CONTRACT["test_lock"]["locked"])
        self.assertEqual(CONTRACT["test_lock"]["access_count_before_freeze"], 0)
        self.assertFalse(CONTRACT["model_selection"]["uses_test_partition"])
        self.assertTrue(CONTRACT["model_selection"]["uses_validation_partition"])
        self.assertFalse(CONTRACT["revision_policy"]["post_test_revision_allowed"])

    def test_scope_firewall(self):
        firewall = CONTRACT["scope_firewall"]
        self.assertFalse(firewall["dqn_allowed"])
        self.assertFalse(firewall["eight_action_training_allowed_initially"])
        self.assertFalse(firewall["p4_rtl_allowed"])
        self.assertEqual(firewall["training_mode"], "offline_only")


if __name__ == "__main__":
    unittest.main(verbosity=2)
