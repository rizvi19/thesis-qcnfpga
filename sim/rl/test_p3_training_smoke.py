"""Tests for the bounded deterministic P3 Step 5 training smoke path."""

import tempfile
from pathlib import Path
import unittest

from rl.h4_trainer import (
    EPISODE_LENGTH,
    FROZEN_TRAIN_SEEDS,
    FULL_SPEC,
    FULL_TRANSITIONS,
    SMOKE_SPEC,
    TrainingSpec,
    train_candidate,
)
from rl.training_smoke import SMOKE_TRAINER_SEEDS, run_smoke, write_smoke_evidence


class TestTrainingSpecification(unittest.TestCase):
    def test_smoke_is_exactly_one_percent_of_full_budget(self):
        self.assertEqual(SMOKE_SPEC.epochs, 2)
        self.assertEqual(SMOKE_SPEC.train_seeds, FROZEN_TRAIN_SEEDS)
        self.assertEqual(SMOKE_SPEC.episode_length, EPISODE_LENGTH)
        self.assertEqual(SMOKE_SPEC.transitions, 8192)
        self.assertEqual(FULL_SPEC.transitions, FULL_TRANSITIONS)
        self.assertEqual(SMOKE_SPEC.transitions / FULL_TRANSITIONS, 0.01)

    def test_only_frozen_train_seeds_are_accepted(self):
        TrainingSpec(1, (101, 211)).validate()
        for forbidden in ((1009,), (2003,), (101, 101), ()):
            with self.assertRaises(ValueError):
                TrainingSpec(1, forbidden).validate()

    def test_only_frozen_trainer_seeds_are_accepted(self):
        with self.assertRaises(ValueError):
            train_candidate(999, TrainingSpec(1, (101,), 2))


class TestCandidateTraining(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tiny_spec = TrainingSpec(epochs=1, train_seeds=(101,), episode_length=16)
        cls.first = train_candidate(17, cls.tiny_spec)
        cls.repeat = train_candidate(17, cls.tiny_spec)
        cls.other = train_candidate(29, cls.tiny_spec)

    def test_same_seed_is_bit_reproducible(self):
        self.assertEqual(self.first, self.repeat)
        self.assertEqual(self.first.q_table_sha256, self.repeat.q_table_sha256)
        self.assertEqual(self.first.policy_sha256, self.repeat.policy_sha256)

    def test_different_trainer_seed_changes_learning_state(self):
        self.assertNotEqual(self.first.q_table_sha256, self.other.q_table_sha256)

    def test_candidate_shapes_and_counts_are_valid(self):
        self.assertEqual(len(self.first.q_table), 256)
        self.assertTrue(all(len(row) == 4 for row in self.first.q_table))
        self.assertEqual(len(self.first.policy), 256)
        self.assertEqual(sum(self.first.final_profile_counts), self.tiny_spec.transitions)
        self.assertEqual(self.first.epochs[-1].cumulative_transitions, self.tiny_spec.transitions)

    def test_trace_hash_is_stable_across_trainer_seeds(self):
        self.assertEqual(self.first.trace_sha256, self.other.trace_sha256)
        self.assertEqual(set(self.first.trace_sha256), {101})


class TestCanonicalSmokeEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = run_smoke()

    def test_two_smoke_candidates_complete_declared_budget(self):
        self.assertEqual(tuple(result.trainer_seed for result in self.results), SMOKE_TRAINER_SEEDS)
        for result in self.results:
            self.assertEqual(result.epochs[-1].cumulative_transitions, 8192)
            self.assertEqual(sum(result.final_profile_counts), 8192)
            self.assertEqual(len(result.epochs), 2)

    def test_different_smoke_seeds_produce_distinct_q_tables(self):
        self.assertNotEqual(self.results[0].q_table_sha256, self.results[1].q_table_sha256)

    def test_evidence_is_byte_deterministic_and_preserves_locks(self):
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = write_smoke_evidence(Path(first_dir))
            second = write_smoke_evidence(Path(second_dir))
            first_files = {path.name: path.read_bytes() for path in Path(first_dir).iterdir()}
            second_files = {path.name: path.read_bytes() for path in Path(second_dir).iterdir()}
            self.assertEqual(first_files, second_files)
            self.assertEqual(first, second)
        manifest = first["manifest"]
        self.assertEqual(manifest["partitions_accessed"], ["train"])
        self.assertEqual(manifest["validation_access_count"], 0)
        self.assertEqual(manifest["test_access_count"], 0)
        self.assertTrue(manifest["test_partition_locked"])
        self.assertFalse(manifest["full_h4_training_performed"])
        self.assertFalse(manifest["model_selection_performed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
