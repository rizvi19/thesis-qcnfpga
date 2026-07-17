"""Tests for the P2 deterministic sensitivity and route-selection boundary."""

import unittest

from rl.h2_profile_adapter import run_h2_action, select_h2_route
from rl.profile_codebook import profile_by_action
from rl.sensitivity_sweep import (
    LONG_PATH,
    LOWER_PATH,
    SCENARIOS,
    SHORT_PATH,
    UPPER_PATH,
    evaluate_scenario,
    run_sweep,
)


EXPECTED_SELECTIONS = {
    "scarcity_protection": ((1.5, 1.5, 1.0, 2.0), (1, 1, 2)),
    "fidelity_protection": ((1.0, 2.0, 0.5, 3.0), (1, 2, 1)),
    "low_latency": ((0.5, 1.0, 0.5, 1.0), (2, 1, 1)),
}


class TestSensitivityProtocol(unittest.TestCase):
    def test_all_scenario_paths_are_simple_ring6_paths(self):
        adjacency = {
            0: {1, 5},
            1: {0, 2},
            2: {1, 3},
            3: {2, 4},
            4: {3, 5},
            5: {0, 4},
        }
        for scenario in SCENARIOS:
            for path_case in scenario.paths:
                self.assertEqual(len(path_case.path), len(set(path_case.path)))
                for source, destination in zip(path_case.path, path_case.path[1:]):
                    self.assertIn(destination, adjacency[source])

    def test_sweep_selects_expected_minimal_profiles(self):
        selected, _ = run_sweep()
        for intent, (alphas, ratio) in EXPECTED_SELECTIONS.items():
            self.assertEqual(selected[intent].alphas, alphas)
            self.assertEqual(selected[intent].lambda_tch_hw_ratio, ratio)

    def test_selected_profiles_pass_every_intent_fixture(self):
        selected, _ = run_sweep()
        for intent, profile in selected.items():
            for scenario in SCENARIOS:
                selection = evaluate_scenario(profile, scenario)
                self.assertEqual(
                    selection.selected.objectives.path,
                    scenario.expected_by_intent[intent],
                )
                self.assertGreaterEqual(selection.score_margin, 0.19)

    def test_profiles_produce_distinct_resource_fidelity_decisions(self):
        selected, _ = run_sweep()
        scenario = SCENARIOS[0]
        scarcity = evaluate_scenario(selected["scarcity_protection"], scenario)
        fidelity = evaluate_scenario(selected["fidelity_protection"], scenario)
        self.assertEqual(scarcity.selected.objectives.path, LOWER_PATH)
        self.assertEqual(fidelity.selected.objectives.path, UPPER_PATH)

    def test_low_latency_selects_short_ring6_path(self):
        selected, _ = run_sweep()
        for scenario in SCENARIOS[-2:]:
            selection = evaluate_scenario(selected["low_latency"], scenario)
            self.assertEqual(selection.selected.objectives.path, SHORT_PATH)

    def test_balanced_h2_route_selection_matches_legacy_first_route(self):
        result = run_h2_action(0)
        selection = select_h2_route(result, profile_by_action(0))
        self.assertEqual(
            selection.selected.objectives.path,
            tuple(result["pareto_front"][0]["path"]),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
