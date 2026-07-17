"""Unit tests for P3 Step 4 deterministic tabular Q-learning mechanics."""

import math
import unittest

from rl.p3_contract import CONTRACT
from rl.q_learning_unit_audit import build_audit
from rl.tabular_q_learning import (
    ACTION_COUNT,
    STATE_COUNT,
    TabularQLearner,
    XorShift32,
    deployment_action,
    epsilon_at,
    extract_policy,
    maximizing_actions,
    new_q_table,
    q_update,
    training_action,
    validate_q_table,
)


class Reward:
    def __init__(self, total):
        self.total = total


class Result:
    def __init__(self, state_id, action_id, reward, next_state_id, done):
        self.state_id = state_id
        self.action_id = action_id
        self.reward = Reward(reward)
        self.next_state_id = next_state_id
        self.done = done


class TinyEnvironment:
    """Three-transition synthetic episode; it is not a frozen QFlow trace."""

    def __init__(self):
        self.index = 0
        self.done = False
        self.states = (3, 7, 3)
        self.rewards = (1.0, -0.5, 2.0)

    def current_state_id(self):
        if self.done:
            raise RuntimeError("terminal")
        return self.states[self.index]

    def step(self, action_id):
        state_id = self.current_state_id()
        reward = self.rewards[self.index]
        self.index += 1
        self.done = self.index == len(self.states)
        next_state_id = None if self.done else self.states[self.index]
        return Result(state_id, action_id, reward, next_state_id, self.done)


class TestXorShift32(unittest.TestCase):
    def test_known_seed_17_sequence(self):
        rng = XorShift32(17)
        self.assertEqual(
            [rng.next_u32() for _ in range(5)],
            [4596240, 1150042706, 1409999377, 22020245, 689350324],
        )

    def test_seed_and_randbelow_validation(self):
        for invalid in (0, -1, 2**32, True, 1.5):
            with self.assertRaises(ValueError):
                XorShift32(invalid)
        with self.assertRaises(ValueError):
            XorShift32(1).randbelow(0)

    def test_fisher_yates_is_deterministic_permutation(self):
        values = tuple(CONTRACT["partitions"]["train_seeds"])
        first = XorShift32(17).shuffled(values)
        second = XorShift32(17).shuffled(values)
        self.assertEqual(first, second)
        self.assertEqual(sorted(first), sorted(values))


class TestQTableAndActions(unittest.TestCase):
    def test_shape_and_independent_rows(self):
        table = new_q_table()
        self.assertEqual(len(table), STATE_COUNT)
        self.assertTrue(all(len(row) == ACTION_COUNT for row in table))
        table[0][0] = 5.0
        self.assertEqual(table[1][0], 0.0)

    def test_q_table_validation_rejects_bad_shapes_and_nonfinite(self):
        with self.assertRaises(ValueError):
            validate_q_table([[0.0] * ACTION_COUNT] * (STATE_COUNT - 1))
        table = new_q_table()
        table[1] = [0.0, 0.0]
        with self.assertRaises(ValueError):
            validate_q_table(table)
        table = new_q_table()
        table[1][1] = math.inf
        with self.assertRaises(ValueError):
            validate_q_table(table)

    def test_training_ties_are_seeded_and_deployment_ties_are_smallest(self):
        table = new_q_table()
        table[10] = [1.0, 3.0, 3.0, 0.0]
        self.assertEqual(maximizing_actions(table, 10), (1, 2))
        self.assertEqual(deployment_action(table, 10), 1)
        sequence_a = [training_action(table, 10, 0.0, XorShift32(seed)) for seed in (17, 29, 43, 71)]
        sequence_b = [training_action(table, 10, 0.0, XorShift32(seed)) for seed in (17, 29, 43, 71)]
        self.assertEqual(sequence_a, sequence_b)
        self.assertTrue(set(sequence_a).issubset({1, 2}))

    def test_policy_extraction_is_256_actions(self):
        table = new_q_table()
        table[255][3] = 1.0
        policy = extract_policy(table)
        self.assertEqual(len(policy), 256)
        self.assertTrue(all(0 <= action < 4 for action in policy))
        self.assertEqual(policy[0], 0)
        self.assertEqual(policy[255], 3)

    def test_invalid_states_actions_epsilon_are_rejected(self):
        table = new_q_table()
        for state in (-1, 256, True):
            with self.assertRaises(ValueError):
                deployment_action(table, state)
        for epsilon in (-0.1, 1.1, math.nan):
            with self.assertRaises(ValueError):
                training_action(table, 0, epsilon, XorShift32(17))
        with self.assertRaises(ValueError):
            q_update(table, 0, 4, 0.0, None, True)


class TestScheduleAndUpdate(unittest.TestCase):
    def test_frozen_epsilon_endpoints_and_monotonicity(self):
        total = CONTRACT["training"]["transitions_per_trainer"]
        decay_count = math.ceil(total * 0.8)
        self.assertEqual(epsilon_at(0, total), 1.0)
        self.assertAlmostEqual(epsilon_at(decay_count - 1, total), 0.05)
        self.assertAlmostEqual(epsilon_at(decay_count, total), 0.05)
        self.assertAlmostEqual(epsilon_at(total - 1, total), 0.05)
        points = [epsilon_at(index, total) for index in (0, total // 4, total // 2, decay_count - 1, total - 1)]
        self.assertEqual(points, sorted(points, reverse=True))

    def test_nonterminal_update_exact_math(self):
        table = new_q_table()
        table[6] = [1.0, 2.0, 2.0, -1.0]
        record = q_update(table, 5, 2, 4.0, 6, False, alpha=0.1, gamma=0.95)
        self.assertEqual(record.bootstrap, 2.0)
        self.assertAlmostEqual(record.target, 5.9)
        self.assertAlmostEqual(record.new_value, 0.59)
        self.assertAlmostEqual(table[5][2], 0.59)

    def test_terminal_bootstrap_is_zero(self):
        table = new_q_table()
        table[5][2] = 0.59
        record = q_update(table, 5, 2, -4.0, None, True, alpha=0.1, gamma=0.95)
        self.assertEqual(record.bootstrap, 0.0)
        self.assertAlmostEqual(record.new_value, 0.131)
        with self.assertRaises(ValueError):
            q_update(table, 5, 2, 0.0, 6, True)
        with self.assertRaises(ValueError):
            q_update(table, 5, 2, 0.0, None, False)


class TestLearnerIntegration(unittest.TestCase):
    def test_synthetic_micro_episode_is_byte_reproducible(self):
        first = TabularQLearner(17)
        second = TabularQLearner(17)
        record_a = first.run_episode(TinyEnvironment(), 0, 3)
        record_b = second.run_episode(TinyEnvironment(), 0, 3)
        self.assertEqual(record_a, record_b)
        self.assertEqual(first.q_table, second.q_table)
        self.assertEqual(record_a.transition_count, 3)

    def test_trace_order_rejects_duplicates(self):
        learner = TabularQLearner(17)
        with self.assertRaises(ValueError):
            learner.shuffled_trace_order((101, 101))

    def test_unit_audit_preserves_all_data_locks(self):
        audit = build_audit()
        self.assertEqual(audit["decision"], "PASS")
        self.assertEqual(audit["training_trace_access_count"], 0)
        self.assertEqual(audit["validation_access_count"], 0)
        self.assertEqual(audit["test_access_count"], 0)
        self.assertTrue(audit["test_partition_locked"])
        self.assertFalse(audit["full_h4_training_performed"])
        self.assertFalse(audit["rtl_or_board_work_performed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
