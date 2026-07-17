"""Pre-test unit checks for the P3 Step 7 policy freeze."""

import json
from pathlib import Path
import tempfile
import unittest

from rl.heldout_evaluation import (
    EXPECTED_POLICY_SEMANTIC_SHA256,
    EXPECTED_Q_SEMANTIC_SHA256,
    SELECTED_SEED,
    TEST_SEEDS,
    validate_selected_inputs,
    verify_test_unlock,
    write_policy_freeze,
)


class TestSelectedInputs(unittest.TestCase):
    def test_exact_revised_seed_229_is_selected(self):
        q_table, policy = validate_selected_inputs()
        self.assertEqual(SELECTED_SEED, 229)
        self.assertEqual(len(q_table), 256)
        self.assertEqual(len(policy), 256)
        self.assertEqual(EXPECTED_Q_SEMANTIC_SHA256, "c515a2fef2ec0b658d26600e2939db15dc1dcac984af9ef33f9dde1518026b87")
        self.assertEqual(EXPECTED_POLICY_SEMANTIC_SHA256, "a133e3c7edfd7f592d56b18e46157f70215dd238cd4c23ece2ca018dfca5a5b4")

    def test_test_manifest_is_exact_and_disjoint(self):
        self.assertEqual(TEST_SEEDS, (2003, 2111, 2203, 2309))


class TestFreezeBeforeUnlock(unittest.TestCase):
    def test_freeze_is_byte_reproducible_and_unlock_is_bound(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_path, second_path = Path(first), Path(second)
            first_result = write_policy_freeze(first_path)
            second_result = write_policy_freeze(second_path)
            self.assertEqual(first_result, second_result)
            for name in ("selected_q_table_seed_229.json", "selected_policy_seed_229.json", "training_config_v1.yaml", "freeze_record.json", "test_unlock.json", "SHA256SUMS"):
                self.assertEqual((first_path / name).read_bytes(), (second_path / name).read_bytes())
            policy = verify_test_unlock(first_path)
            self.assertEqual(len(policy), 256)
            freeze = json.loads((first_path / "freeze_record.json").read_text())
            unlock = json.loads((first_path / "test_unlock.json").read_text())
            self.assertEqual(freeze["sequence"], 1)
            self.assertEqual(unlock["sequence"], 2)
            self.assertEqual(freeze["test_access_count_before_freeze"], 0)
            self.assertFalse(unlock["post_unlock_revision_allowed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
