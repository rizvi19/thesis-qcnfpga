"""Checks for deterministic P3 deployment export and claim boundaries."""

import json
from pathlib import Path
import tempfile
import unittest

from rl.p3_export import (
    PROFILE_CODEBOOK,
    SOURCE_POLICY,
    SOURCE_Q,
    decode_profile,
    decode_q_hex,
    encode_profile,
    q_hex_word,
    validate_inputs,
    write_export,
)


class TestEncoding(unittest.TestCase):
    def test_q_fixed_point_known_values(self):
        self.assertEqual(q_hex_word(0.0), "0000")
        self.assertEqual(q_hex_word(1.5), "00C0")
        self.assertEqual(q_hex_word(-1.5), "FF40")
        self.assertEqual(decode_q_hex("00C0"), 1.5)
        self.assertEqual(decode_q_hex("FF40"), -1.5)

    def test_profile_payload_roundtrip(self):
        codebook = json.loads(PROFILE_CODEBOOK.read_text(encoding="utf-8"))
        for profile in codebook["profiles"]:
            payload = encode_profile(profile)
            alphas, ratios = decode_profile(payload)
            self.assertEqual(alphas, tuple(int(round(float(value) * 2)) for value in profile["alphas"]))
            self.assertEqual(ratios, tuple(int(value) for value in profile["lambda_tch_hw_ratio"]))


class TestFrozenExport(unittest.TestCase):
    def test_frozen_inputs_and_shapes(self):
        q_table, policy, codebook = validate_inputs()
        self.assertEqual(len(q_table), 256)
        self.assertEqual(len(policy), 256)
        self.assertEqual(len(codebook["profiles"]), 4)

    def test_export_is_byte_reproducible(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_path, second_path = Path(first), Path(second)
            first_card, second_card = first_path / "model.md", second_path / "model.md"
            first_result = write_export(first_path, first_card)
            second_result = write_export(second_path, second_card)
            self.assertEqual(first_result, second_result)
            for name in ("policy_rom.mem", "q_table.mem", "profile_rom.mem", "rom_layout.json", "export_manifest.json", "SHA256SUMS"):
                self.assertEqual((first_path / name).read_bytes(), (second_path / name).read_bytes())
            self.assertEqual(first_card.read_bytes(), second_card.read_bytes())

    def test_export_roundtrips_and_preserves_policy_argmax(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            manifest = write_export(path, path / "model.md")
            self.assertTrue(manifest["policy_roundtrip_match"])
            self.assertTrue(manifest["profile_roundtrip_match"])
            self.assertEqual(manifest["q_quantization"]["policy_argmax_mismatch_count"], 0)
            self.assertLessEqual(manifest["q_quantization"]["maximum_absolute_error"], 1.0 / 256.0)
            self.assertEqual(len((path / "policy_rom.mem").read_text().splitlines()), 256)
            self.assertEqual(len((path / "q_table.mem").read_text().splitlines()), 1024)
            self.assertEqual(len((path / "profile_rom.mem").read_text().splitlines()), 4)

    def test_model_card_retains_insufficient_power_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            write_export(path, path / "model.md")
            text = (path / "model.md").read_text(encoding="utf-8")
            self.assertIn("not statistical superiority", text)
            self.assertIn("online or on-chip learning is not claimed", text)
            self.assertIn("P3 provides Python/reference-model evidence only", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
