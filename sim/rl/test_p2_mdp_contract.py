"""Boundary and decomposition tests for the frozen P2 MDP contract."""

import unittest

from rl.mdp_contract import (
    CONTRACT,
    RewardInput,
    StateObservation,
    calculate_reward,
    decode_state_id,
    encode_state,
    episode_done,
    feature_bin,
    validate_contract,
)


class TestStateEncoding(unittest.TestCase):
    def test_all_256_state_ids_decode_uniquely(self):
        decoded = [decode_state_id(state_id) for state_id in range(256)]
        self.assertEqual(len(set(decoded)), 256)
        self.assertEqual(decoded[0], (0, 0, 0, 0))
        self.assertEqual(decoded[-1], (3, 3, 3, 3))

    def test_threshold_equality_enters_higher_bin(self):
        for feature_name in CONTRACT["state"]["feature_order"]:
            thresholds = CONTRACT["state"]["features"][feature_name]["thresholds"]
            for expected_bin, threshold in enumerate(thresholds, start=1):
                self.assertEqual(feature_bin(feature_name, threshold), expected_bin)
                self.assertEqual(feature_bin(feature_name, threshold - 1e-9), expected_bin - 1)

    def test_input_clipping(self):
        self.assertEqual(feature_bin("min_key_occupancy", -10.0), 0)
        self.assertEqual(feature_bin("min_key_occupancy", 10.0), 3)

    def test_encoder_radix_order(self):
        observation = StateObservation(
            min_key_occupancy=0.5,
            bottleneck_fidelity=0.93,
            offered_request_load=0.5,
            utilization_imbalance=0.25,
        )
        self.assertEqual(encode_state(observation), 170)
        self.assertEqual(decode_state_id(170), (2, 2, 2, 2))

    def test_invalid_state_id_is_rejected(self):
        for state_id in (-1, 256, 1.5):
            with self.assertRaises(ValueError):
                decode_state_id(state_id)


class TestRewardDecomposition(unittest.TestCase):
    def test_maximum_nominal_success_reward(self):
        reward = calculate_reward(
            RewardInput(
                success=True,
                action_id=0,
                bottleneck_fidelity=1.0,
                post_decision_imbalance=0.0,
                selected_path_hops=1,
            )
        )
        self.assertEqual(reward.success, 4.0)
        self.assertAlmostEqual(reward.fidelity_utility, 2.0)
        self.assertEqual(reward.balance_utility, 1.0)
        self.assertEqual(reward.hop_cost, -0.25)
        self.assertEqual(reward.switch_cost, 0.0)
        self.assertAlmostEqual(reward.total, 6.75)

    def test_blocked_reward_contains_only_block_and_switch(self):
        reward = calculate_reward(
            RewardInput(success=False, action_id=1, previous_action_id=0)
        )
        self.assertEqual(reward.blocking, -4.0)
        self.assertEqual(reward.switch_cost, -0.25)
        self.assertEqual(reward.fidelity_utility, 0.0)
        self.assertEqual(reward.balance_utility, 0.0)
        self.assertEqual(reward.hop_cost, 0.0)
        self.assertEqual(reward.total, -4.25)

    def test_fidelity_component_is_independent(self):
        low = calculate_reward(
            RewardInput(True, 0, bottleneck_fidelity=0.9, post_decision_imbalance=0.5, selected_path_hops=3)
        )
        high = calculate_reward(
            RewardInput(True, 0, bottleneck_fidelity=0.95, post_decision_imbalance=0.5, selected_path_hops=3)
        )
        self.assertEqual(low.fidelity_utility, 0.0)
        self.assertAlmostEqual(high.fidelity_utility, 1.0)
        self.assertAlmostEqual(high.total - low.total, 1.0)

    def test_balance_component_is_independent(self):
        balanced = calculate_reward(
            RewardInput(True, 0, bottleneck_fidelity=0.95, post_decision_imbalance=0.0, selected_path_hops=3)
        )
        imbalanced = calculate_reward(
            RewardInput(True, 0, bottleneck_fidelity=0.95, post_decision_imbalance=1.0, selected_path_hops=3)
        )
        self.assertEqual(balanced.balance_utility, 1.0)
        self.assertEqual(imbalanced.balance_utility, 0.0)
        self.assertAlmostEqual(balanced.total - imbalanced.total, 1.0)

    def test_invalid_action_and_success_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            calculate_reward(RewardInput(success=False, action_id=4))
        with self.assertRaises(ValueError):
            calculate_reward(RewardInput(success=True, action_id=0, selected_path_hops=2))
        with self.assertRaises(ValueError):
            calculate_reward(RewardInput(success=False, action_id=0, selected_path_hops=1))


class TestTransitionAndPartitions(unittest.TestCase):
    def test_no_path_is_not_automatically_terminal(self):
        self.assertFalse(CONTRACT["transition"]["no_path_terminal"])
        self.assertFalse(episode_done(1, 512))
        self.assertTrue(episode_done(512, 512))

    def test_partition_seeds_are_disjoint(self):
        partitions = CONTRACT["partitions"]
        train = set(partitions["train_seeds"])
        validation = set(partitions["validation_seeds"])
        test = set(partitions["test_seeds"])
        self.assertFalse(train & validation)
        self.assertFalse(train & test)
        self.assertFalse(validation & test)

    def test_contract_validation_summary(self):
        summary = validate_contract()
        self.assertEqual(summary["state_count"], 256)
        self.assertEqual(summary["action_count"], 4)
        self.assertEqual(summary["reward_bounds"], [-4.25, 6.75])
        self.assertFalse(summary["dqn_allowed_in_p2"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
