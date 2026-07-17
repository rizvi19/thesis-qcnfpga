"""Tests for deterministic Ring-6 traces and MDP transition order."""

import hashlib
import unittest

from rl.ring6_environment import KEY_CAPACITY, Ring6Environment
from rl.trace_generator import (
    RING_EDGES,
    LinkInitialState,
    LinkUpdate,
    Ring6Trace,
    TraceRecord,
    build_manual_trace,
    canonical_trace_bytes,
    generate_trace,
    ring_paths,
)


def _uniform_trace(key_count: int, record_count: int, arrivals: int = 0) -> Ring6Trace:
    initial = tuple(LinkInitialState(key_count, 0.97, 4.0, 0.03) for _ in RING_EDGES)
    updates = tuple(LinkUpdate(arrivals, 0.97, 4.0, 0.03) for _ in RING_EDGES)
    records = tuple(TraceRecord(0, 3, 1, updates, "test") for _ in range(record_count))
    return Ring6Trace("uniform_test", 0, initial, records)


class TestTraceGenerator(unittest.TestCase):
    def test_ring_paths_cover_both_simple_directions(self):
        self.assertEqual(ring_paths(0, 3), ((0, 1, 2, 3), (0, 5, 4, 3)))
        self.assertEqual(ring_paths(0, 2), ((0, 1, 2), (0, 5, 4, 3, 2)))

    def test_same_seed_is_byte_identical(self):
        first = canonical_trace_bytes(generate_trace(101, 64))
        second = canonical_trace_bytes(generate_trace(101, 64))
        self.assertEqual(first, second)

    def test_different_seeds_change_trace(self):
        first = hashlib.sha256(canonical_trace_bytes(generate_trace(101, 64))).digest()
        second = hashlib.sha256(canonical_trace_bytes(generate_trace(211, 64))).digest()
        self.assertNotEqual(first, second)

    def test_manual_trace_is_fixed_length(self):
        trace = build_manual_trace()
        self.assertEqual(len(trace.records), 8)
        self.assertEqual(trace.trace_id, "manual_ring6_v0")


class TestEnvironmentTransitions(unittest.TestCase):
    def test_reset_and_terminal_behavior(self):
        environment = Ring6Environment(_uniform_trace(8, 2))
        self.assertTrue(0 <= environment.current_state_id() < 256)
        first = environment.step(0)
        self.assertFalse(first.done)
        second = environment.step(0)
        self.assertTrue(second.done)
        self.assertIsNone(second.next_state_id)
        with self.assertRaises(RuntimeError):
            environment.step(0)

    def test_no_path_is_blocked_but_not_early_terminal(self):
        environment = Ring6Environment(_uniform_trace(0, 2))
        first = environment.step(0)
        self.assertFalse(first.success)
        self.assertFalse(first.done)
        self.assertEqual(first.reward.blocking, -4.0)
        self.assertEqual(first.reward.total, -4.0)

    def test_consumption_happens_before_arrival(self):
        environment = Ring6Environment(_uniform_trace(1, 1, arrivals=1))
        result = environment.step(0)
        self.assertTrue(result.success)
        selected_edges = tuple(zip(result.selected_path, result.selected_path[1:]))
        for edge in selected_edges:
            self.assertEqual(environment.links[edge].key_count, 1)

    def test_key_count_is_saturated_at_capacity(self):
        environment = Ring6Environment(_uniform_trace(KEY_CAPACITY, 1, arrivals=1))
        environment.step(0)
        for link in environment.links.values():
            self.assertLessEqual(link.key_count, KEY_CAPACITY)

    def test_reward_components_sum_to_total(self):
        result = Ring6Environment(_uniform_trace(8, 1)).step(2)
        components = result.reward
        expected = (
            components.success
            + components.blocking
            + components.fidelity_utility
            + components.balance_utility
            + components.hop_cost
            + components.switch_cost
        )
        self.assertAlmostEqual(result.reward.total, expected)

    def test_invalid_action_is_rejected_without_advancing(self):
        environment = Ring6Environment(_uniform_trace(8, 2))
        with self.assertRaises(ValueError):
            environment.step(4)
        self.assertEqual(environment.trace_index, 0)

    def test_manual_action_replay_is_deterministic(self):
        actions = (0, 1, 2, 3, 0, 1, 2, 3)
        first = Ring6Environment(build_manual_trace())
        second = Ring6Environment(build_manual_trace())
        first_log = [first.step(action) for action in actions]
        second_log = [second.step(action) for action in actions]
        self.assertEqual(first_log, second_log)
        self.assertTrue(first_log[-1].done)
        self.assertTrue(all(item.success for item in first_log))


if __name__ == "__main__":
    unittest.main(verbosity=2)
