"""P2 profile-codebook and parameterized-H2 regression tests."""

import hashlib
import json
import unittest

import reference_model
from rl.h2_profile_adapter import run_h2_action
from rl.profile_codebook import PROFILES, profile_by_action


EXPECTED_H2_HASH = "e4a393bc349f064ab7709e75fe6093210cf05f6f842fee33d4cc5b0adbcdaf3f"


def canonical_bytes(result: dict) -> bytes:
    return json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


class TestProfileCodebook(unittest.TestCase):
    def test_exactly_four_actions(self):
        self.assertEqual(tuple(profile.action_id for profile in PROFILES), (0, 1, 2, 3))

    def test_balanced_profile_is_frozen_h2_anchor(self):
        balanced = profile_by_action(0)
        self.assertEqual(balanced.alphas, (1.0, 1.5, 0.5, 2.0))
        self.assertEqual(balanced.lambda_tch, (0.4, 0.4, 0.2))
        self.assertEqual(balanced.status, "frozen_h2_anchor")

    def test_adaptive_profiles_have_controlled_maturity(self):
        for profile in PROFILES[1:]:
            self.assertIn(
                profile.status,
                {"candidate_pending_sensitivity", "selected_p2_sensitivity"},
            )

    def test_alpha_candidates_are_shift_add_friendly(self):
        for profile in PROFILES:
            for coefficient in profile.alphas:
                self.assertEqual(coefficient * 2.0, round(coefficient * 2.0))

    def test_hardware_ratios_preserve_lambda_tch_proportions(self):
        for profile in PROFILES:
            ratios = profile.lambda_tch_hw_ratio
            normalized = tuple(value / sum(ratios) for value in ratios)
            for actual, expected in zip(normalized, profile.lambda_tch):
                self.assertAlmostEqual(actual, expected, places=12)

    def test_invalid_action_is_rejected(self):
        with self.assertRaises(ValueError):
            profile_by_action(4)


class TestParameterizedH2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default_result = reference_model.run_ring6_experiment(verbose=False)
        cls.balanced_result = run_h2_action(0)

    def test_default_h2_hash_is_unchanged(self):
        digest = hashlib.sha256(canonical_bytes(self.default_result)).hexdigest()
        self.assertEqual(digest, EXPECTED_H2_HASH)

    def test_forced_balanced_is_byte_identical_to_h2(self):
        self.assertEqual(canonical_bytes(self.default_result), canonical_bytes(self.balanced_result))


if __name__ == "__main__":
    unittest.main(verbosity=2)
