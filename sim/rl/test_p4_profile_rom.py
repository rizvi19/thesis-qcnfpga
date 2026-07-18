"""Independent P4 Step 5 tests for the frozen four-entry profile ROM."""

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

from rl.p3_export import decode_profile, encode_profile, validate_inputs


REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE_MEM = REPO_ROOT / "results/rl/p3_export/profile_rom.mem"
SHA_MANIFEST = REPO_ROOT / "results/rl/p3_export/SHA256SUMS"
LAYOUT_PATH = REPO_ROOT / "results/rl/p3_export/rom_layout.json"
EXPORT_MANIFEST = REPO_ROOT / "results/rl/p3_export/export_manifest.json"
CONTRACT_PATH = REPO_ROOT / "rl/config/p4_rtl_contract_v1.json"
RTL_PATH = REPO_ROOT / "rtl/rl/rl_profile_rom.v"
GENERATOR_PATH = REPO_ROOT / "sim/rl/p4_generate_profile_rom_vectors.py"
CSV_PATH = REPO_ROOT / "sim/rl/p4_profile_rom_vectors.csv"
RTL_VECTOR_PATH = REPO_ROOT / "sim/rl/p4_profile_rom_vectors.txt"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_words():
    lines = PROFILE_MEM.read_text(encoding="ascii").splitlines()
    if len(lines) != 4 or any(re.fullmatch(r"[0-3][0-9A-F]{4}", line) is None for line in lines):
        raise AssertionError("profile_rom.mem physical format changed")
    return tuple(int(line, 16) for line in lines)


def load_rows():
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class TestFrozenProfileArtifact(unittest.TestCase):
    def test_checksum_layout_and_72_bit_contract_are_exact(self):
        matching = []
        for line in SHA_MANIFEST.read_text(encoding="utf-8").splitlines():
            match = re.fullmatch(r"([0-9a-fA-F]{64})\s+[ *](.+)", line.strip())
            if match and Path(match.group(2)).name == "profile_rom.mem":
                matching.append(match.group(1).lower())
        self.assertEqual(matching, [digest(PROFILE_MEM)])
        layout = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))["profile_rom"]
        self.assertEqual(layout["depth"], 4)
        self.assertEqual(layout["payload_bits"], 18)
        self.assertEqual(layout["file_hex_digits_per_word"], 5)
        self.assertEqual(len(layout["field_order_msb_to_lsb"]), 7)
        self.assertEqual(layout["depth"] * layout["payload_bits"], 72)
        manifest = json.loads(EXPORT_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["profile_entry_count"], 4)
        self.assertEqual(manifest["profile_payload_bits_total"], 72)
        self.assertTrue(manifest["profile_roundtrip_match"])

    def test_memory_exactly_matches_action_major_frozen_codebook(self):
        words = read_words()
        _q_table, _policy, codebook = validate_inputs()
        expected = tuple(encode_profile(profile) for profile in codebook["profiles"])
        self.assertEqual(words, expected)
        self.assertEqual(len(set(words)), 4)
        self.assertTrue(all(0 <= word < (1 << 18) for word in words))
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        profile = contract["profile_rom"]
        self.assertEqual(profile["deployment_artifact"], "results/rl/p3_export/profile_rom.mem")
        self.assertEqual(profile["depth"], 4)
        self.assertEqual(profile["payload_width_bits_per_profile"], 18)
        self.assertEqual(profile["complete_rom_payload_bits"], 72)

    def test_every_payload_roundtrips_to_exact_frozen_coefficients(self):
        words = read_words()
        _q_table, _policy, codebook = validate_inputs()
        for action, (word, profile) in enumerate(zip(words, codebook["profiles"])):
            alphas, ratios = decode_profile(word)
            expected_alphas = tuple(int(round(float(value) * 2)) for value in profile["alphas"])
            expected_ratios = tuple(int(value) for value in profile["lambda_tch_hw_ratio"])
            self.assertEqual(alphas, expected_alphas, f"alpha mismatch at action {action}")
            self.assertEqual(ratios, expected_ratios, f"ratio mismatch at action {action}")


class TestProfileVectors(unittest.TestCase):
    def test_all_four_action_payloads_agree_exactly(self):
        words = read_words()
        rows = [row for row in load_rows() if row["category"] == "all_four_actions"]
        self.assertEqual(len(rows), 4)
        self.assertEqual({int(row["selected_action"]) for row in rows}, {0, 1, 2, 3})
        for row in rows:
            action = int(row["selected_action"])
            self.assertEqual(int(row["expected_valid"]), 1)
            self.assertEqual(int(row["expected_profile_payload_decimal"]), words[action])
            self.assertEqual(row["expected_profile_payload_hex"], f"{words[action]:05X}")

    def test_reset_enable_hold_and_post_reset_read_are_deterministic(self):
        words = read_words()
        rows = load_rows()
        self.assertEqual(len(rows), 8)
        held = 0
        for expected_case, row in enumerate(rows):
            self.assertEqual(int(row["case_id"]), expected_case)
            rst = int(row["rst"])
            en = int(row["en"])
            action = int(row["selected_action"])
            if rst:
                held = 0
                expected_valid = 0
            elif en:
                held = words[action]
                expected_valid = 1
            else:
                expected_valid = 0
            self.assertEqual(int(row["expected_valid"]), expected_valid)
            self.assertEqual(int(row["expected_profile_payload_decimal"]), held)
            self.assertEqual(row["expected_profile_payload_hex"], f"{held:05X}")

    def test_numeric_rtl_vectors_match_reviewable_csv(self):
        rows = load_rows()
        lines = RTL_VECTOR_PATH.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), len(rows))
        columns = (
            "case_id",
            "rst",
            "en",
            "selected_action",
            "expected_valid",
            "expected_profile_payload_decimal",
        )
        for row, line in zip(rows, lines):
            self.assertEqual(tuple(map(int, line.split())), tuple(int(row[name]) for name in columns))

    def test_generator_is_byte_reproducible(self):
        spec = importlib.util.spec_from_file_location("p4_profile_generator", GENERATOR_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        words = module.read_frozen_profiles()
        rows = module.build_vectors(words)
        with tempfile.TemporaryDirectory() as directory:
            csv_output = Path(directory) / "vectors.csv"
            rtl_output = Path(directory) / "vectors.txt"
            module.write_vectors(rows, csv_output, rtl_output)
            self.assertEqual(csv_output.read_bytes(), CSV_PATH.read_bytes())
            self.assertEqual(rtl_output.read_bytes(), RTL_VECTOR_PATH.read_bytes())


class TestProfileRomRTL(unittest.TestCase):
    def test_rtl_is_registered_verilog_2001_and_reads_frozen_memory(self):
        text = RTL_PATH.read_text(encoding="utf-8")
        required = (
            "module rl_profile_rom",
            'parameter MEM_FILE = "results/rl/p3_export/profile_rom.mem"',
            "reg [17:0] profile_mem [0:3];",
            "$readmemh(MEM_FILE, profile_mem);",
            "always @(posedge clk)",
            "valid           <= 1'b0;",
            "profile_payload <= 18'd0;",
            "valid <= en;",
            "profile_payload <= profile_mem[selected_action];",
        )
        for token in required:
            self.assertIn(token, text)
        for forbidden in ("always_ff", "always_comb", "logic ", "typedef", "package ", "interface "):
            self.assertNotIn(forbidden, text)
        self.assertEqual(text.count("initial begin"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
