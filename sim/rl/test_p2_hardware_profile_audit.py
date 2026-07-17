"""Tests for exact shift/add representation of the selected P2 profiles."""

from fractions import Fraction
import unittest

from rl.hardware_profile_audit import (
    ALPHA_FRACTION_BITS,
    ALPHA_NUMERATOR_BITS,
    CODEBOOK_ROM_PAYLOAD_BITS,
    LAMBDA_RATIO_BITS,
    PROFILE_ROM_PAYLOAD_BITS,
    audit_summary,
    decode_alpha,
    encode_alpha,
    integer_ratio_selected_path,
    normalized_ratio,
    route_equivalence_rows,
    shift_positions,
)
from rl.profile_codebook import PROFILES
from rl.route_selector import select_route
from rl.sensitivity_sweep import SCENARIOS, evaluate_path


class TestAlphaEncoding(unittest.TestCase):
    def test_known_alpha_numerators(self):
        expected = {
            "balanced": (2, 3, 1, 4),
            "scarcity_protection": (3, 3, 2, 4),
            "fidelity_protection": (2, 4, 1, 6),
            "low_latency": (1, 2, 1, 2),
        }
        for profile in PROFILES:
            self.assertEqual(tuple(encode_alpha(value) for value in profile.alphas), expected[profile.key])

    def test_all_alpha_values_roundtrip_exactly(self):
        for profile in PROFILES:
            for value in profile.alphas:
                self.assertEqual(decode_alpha(encode_alpha(value)), Fraction(str(value)))

    def test_alpha_shift_add_bound(self):
        self.assertEqual(ALPHA_FRACTION_BITS, 1)
        self.assertEqual(ALPHA_NUMERATOR_BITS, 3)
        for profile in PROFILES:
            for value in profile.alphas:
                self.assertLessEqual(len(shift_positions(encode_alpha(value))), 2)

    def test_non_dyadic_and_overflowing_alpha_values_are_rejected(self):
        for value in (0.25, 0.75, 4.0, 8.0, 0.0, -1.0, float("inf"), True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    encode_alpha(value)


class TestLambdaRatioEncoding(unittest.TestCase):
    def test_ratios_reproduce_normalized_lambdas_exactly(self):
        for profile in PROFILES:
            expected = tuple(Fraction(str(value)) for value in profile.lambda_tch)
            self.assertEqual(normalized_ratio(profile.lambda_tch_hw_ratio), expected)

    def test_ratio_fields_are_single_shift_terms(self):
        self.assertEqual(LAMBDA_RATIO_BITS, 2)
        for profile in PROFILES:
            for value in profile.lambda_tch_hw_ratio:
                self.assertEqual(len(shift_positions(value)), 1)

    def test_profile_rom_payload_budget(self):
        self.assertEqual(PROFILE_ROM_PAYLOAD_BITS, 18)
        self.assertEqual(CODEBOOK_ROM_PAYLOAD_BITS, 72)


class TestRouteEquivalence(unittest.TestCase):
    def test_integer_ratios_match_float_weights_on_all_scenarios(self):
        checks = 0
        for profile in PROFILES:
            for scenario in SCENARIOS:
                candidates = tuple(evaluate_path(profile, path_case) for path_case in scenario.paths)
                expected = select_route(candidates, profile.lambda_tch).selected.objectives.path
                self.assertEqual(integer_ratio_selected_path(candidates, profile.lambda_tch_hw_ratio), expected)
                checks += 1
        self.assertEqual(checks, 20)

    def test_integer_ratios_match_all_canonical_h2_fronts(self):
        rows = [item for item in route_equivalence_rows() if item["source"] == "canonical_h2_pareto"]
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(item["match"] for item in rows))

    def test_complete_hardware_audit_passes(self):
        summary = audit_summary()
        self.assertTrue(summary["p2_hardware_coefficient_gate_passed"])
        self.assertEqual(summary["exact_alpha_roundtrip_count"], 4)
        self.assertEqual(summary["exact_lambda_ratio_count"], 4)
        self.assertEqual(summary["route_equivalence_checks"], 24)
        self.assertEqual(summary["route_equivalence_matches"], 24)
        self.assertEqual(summary["generic_profile_multiplier_budget"], 0)
        self.assertFalse(summary["rtl_or_synthesis_claimed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
