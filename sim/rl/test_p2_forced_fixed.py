"""Forced-Balanced H2 regression and exhaustive environment edge tests."""

import hashlib
import math
import unittest

from rl.forced_fixed_regression import (
    FROZEN_H2_SHA256,
    canonical_step_bytes,
    forced_balanced_replay,
    h2_regression_summary,
)
from rl.mdp_contract import CONTRACT, RewardInput, calculate_reward, decode_state_id
from rl.profile_codebook import profile_by_action
from rl.ring6_environment import FIDELITY_FLOOR, Ring6Environment
from rl.trace_generator import RING_EDGES, LinkInitialState, LinkUpdate, Ring6Trace, TraceRecord, build_manual_trace, generate_trace


def _trace_with_links(initial_links, *, records=1, src=0, dst=3, updates=None):
    if updates is None:
        updates = tuple(LinkUpdate(0, item.fidelity, item.key_rate, item.qber) for item in initial_links)
    trace_records = tuple(TraceRecord(src, dst, 1, tuple(updates), "edge_test") for _ in range(records))
    return Ring6Trace("edge_test", 0, tuple(initial_links), trace_records)


def _uniform_links(key_count=8, fidelity=0.97, key_rate=4.0, qber=0.03):
    return [LinkInitialState(key_count, fidelity, key_rate, qber) for _ in RING_EDGES]


class TestForcedBalancedGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = h2_regression_summary()

    def test_forced_balanced_is_exact_canonical_h2(self):
        self.assertTrue(self.summary["canonical_json_byte_identical"])
        self.assertEqual(self.summary["legacy_h2_sha256"], FROZEN_H2_SHA256)
        self.assertEqual(self.summary["forced_balanced_h2_sha256"], FROZEN_H2_SHA256)

    def test_balanced_selector_preserves_legacy_route(self):
        self.assertTrue(self.summary["route_selection_parity"])
        self.assertEqual(self.summary["balanced_selected_route"], self.summary["legacy_first_route"])

    def test_gate_does_not_claim_dynamic_trace_equivalence(self):
        self.assertFalse(self.summary["dynamic_trace_equivalence_claimed"])

    def test_manual_replay_is_fully_clamped_and_repeatable(self):
        first = forced_balanced_replay(build_manual_trace())
        second = forced_balanced_replay(build_manual_trace())
        self.assertEqual(canonical_step_bytes(first), canonical_step_bytes(second))
        self.assertTrue(all(item.action_id == 0 and item.profile_key == "balanced" for item in first))
        self.assertTrue(first[-1].done)

    def test_all_partition_traces_reach_terminal_under_clamp(self):
        count = 0
        for key in ("train_seeds", "validation_seeds", "test_seeds"):
            for seed in CONTRACT["partitions"][key]:
                trace = generate_trace(int(seed), int(CONTRACT["partitions"]["episode_length"]))
                first = forced_balanced_replay(trace)
                second = forced_balanced_replay(trace)
                self.assertEqual(hashlib.sha256(canonical_step_bytes(first)).digest(), hashlib.sha256(canonical_step_bytes(second)).digest())
                self.assertEqual(len(first), 512)
                self.assertTrue(first[-1].done)
                self.assertTrue(all(item.action_id == 0 for item in first))
                count += 1
        self.assertEqual(count, 16)


class TestEnvironmentFeasibilityEdges(unittest.TestCase):
    def test_only_clockwise_route_is_selected(self):
        links = _uniform_links()
        links[RING_EDGES.index((0, 5))] = LinkInitialState(0, 0.97, 4.0, 0.03)
        result = Ring6Environment(_trace_with_links(links)).step(0)
        self.assertEqual(result.selected_path, (0, 1, 2, 3))

    def test_only_counterclockwise_route_is_selected(self):
        links = _uniform_links()
        links[RING_EDGES.index((0, 1))] = LinkInitialState(0, 0.97, 4.0, 0.03)
        result = Ring6Environment(_trace_with_links(links)).step(0)
        self.assertEqual(result.selected_path, (0, 5, 4, 3))

    def test_equal_routes_have_deterministic_lexicographic_tie_break(self):
        trace = _trace_with_links(_uniform_links())
        paths = [Ring6Environment(trace).step(action).selected_path for action in range(4)]
        self.assertEqual(paths, [(0, 1, 2, 3)] * 4)

    def test_each_infeasibility_reason_can_block_both_routes(self):
        cases = (
            _uniform_links(key_count=0),
            _uniform_links(fidelity=FIDELITY_FLOOR - 0.0001),
            _uniform_links(key_rate=0.0),
        )
        for links in cases:
            with self.subTest(links=links[0]):
                result = Ring6Environment(_trace_with_links(links)).step(0)
                self.assertFalse(result.success)
                self.assertEqual(result.reward.total, -4.0)

    def test_fidelity_floor_is_inclusive(self):
        result = Ring6Environment(_trace_with_links(_uniform_links(fidelity=FIDELITY_FLOOR))).step(0)
        self.assertTrue(result.success)


class TestEnvironmentValidationEdges(unittest.TestCase):
    def test_all_invalid_action_forms_are_rejected_without_advance(self):
        environment = Ring6Environment(_trace_with_links(_uniform_links(), records=2))
        for action in (-1, 4, True, 1.0, "0", None):
            with self.subTest(action=action):
                with self.assertRaises(ValueError):
                    environment.step(action)
                self.assertEqual(environment.trace_index, 0)
                self.assertIsNone(environment.previous_action_id)

    def test_profile_and_state_identifiers_reject_boolean_aliases(self):
        with self.assertRaises(ValueError):
            profile_by_action(True)
        with self.assertRaises(ValueError):
            decode_state_id(False)
        with self.assertRaises(ValueError):
            calculate_reward(RewardInput(success=False, action_id=True))
        with self.assertRaises(ValueError):
            calculate_reward(RewardInput(success=False, action_id=0, previous_action_id=False))

    def test_nonfinite_and_out_of_range_initial_metrics_are_rejected(self):
        bad_links = (
            _uniform_links(key_count=17),
            _uniform_links(fidelity=math.nan),
            _uniform_links(fidelity=1.01),
            _uniform_links(key_rate=-1.0),
            _uniform_links(qber=-0.01),
        )
        for links in bad_links:
            with self.subTest(link=links[0]):
                with self.assertRaises(ValueError):
                    Ring6Environment(_trace_with_links(links))

    def test_malformed_record_is_rejected_before_any_transition(self):
        links = _uniform_links()
        short_updates = tuple(LinkUpdate(0, 0.97, 4.0, 0.03) for _ in RING_EDGES[:-1])
        with self.assertRaises(ValueError):
            Ring6Environment(_trace_with_links(links, updates=short_updates))
        with self.assertRaises(ValueError):
            Ring6Environment(_trace_with_links(links, src=0, dst=0))
        with self.assertRaises(ValueError):
            Ring6Environment(_trace_with_links(links, src=True, dst=3))

    def test_invalid_updates_are_rejected_before_any_transition(self):
        links = _uniform_links()
        bad_updates = (
            LinkUpdate(-1, 0.97, 4.0, 0.03),
            LinkUpdate(0, math.inf, 4.0, 0.03),
            LinkUpdate(0, 0.97, -1.0, 0.03),
            LinkUpdate(0, 0.97, 4.0, 1.01),
        )
        for bad in bad_updates:
            updates = [LinkUpdate(0, 0.97, 4.0, 0.03) for _ in RING_EDGES]
            updates[0] = bad
            with self.subTest(update=bad):
                with self.assertRaises(ValueError):
                    Ring6Environment(_trace_with_links(links, updates=updates))

    def test_reset_restores_exact_forced_replay(self):
        environment = Ring6Environment(build_manual_trace())
        initial_state = environment.current_state_id()
        first = tuple(environment.step(0) for _ in range(len(environment.trace.records)))
        self.assertTrue(first[-1].done)
        self.assertEqual(environment.reset(), initial_state)
        second = tuple(environment.step(0) for _ in range(len(environment.trace.records)))
        self.assertEqual(canonical_step_bytes(first), canonical_step_bytes(second))


if __name__ == "__main__":
    unittest.main(verbosity=2)
