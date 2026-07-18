"""Independent P4 Step 4 tests for the frozen learned policy ROM."""

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

from rl.p3_export import validate_inputs


REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_MEM = REPO_ROOT / "results/rl/p3_export/policy_rom.mem"
SHA_MANIFEST = REPO_ROOT / "results/rl/p3_export/SHA256SUMS"
LAYOUT_PATH = REPO_ROOT / "results/rl/p3_export/rom_layout.json"
EXPORT_MANIFEST = REPO_ROOT / "results/rl/p3_export/export_manifest.json"
CONTRACT_PATH = REPO_ROOT / "rl/config/p4_rtl_contract_v1.json"
RTL_PATH = REPO_ROOT / "rtl/rl/rl_policy_rom.v"
GENERATOR_PATH = REPO_ROOT / "sim/rl/p4_generate_policy_rom_vectors.py"
CSV_PATH = REPO_ROOT / "sim/rl/p4_policy_rom_vectors.csv"
RTL_VECTOR_PATH = REPO_ROOT / "sim/rl/p4_policy_rom_vectors.txt"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_policy():
    lines = POLICY_MEM.read_text(encoding="ascii").splitlines()
    if len(lines) != 256 or any(re.fullmatch(r"[0-3]", line) is None for line in lines):
        raise AssertionError("policy_rom.mem does not have the exact frozen physical format")
    return tuple(int(line, 16) for line in lines)


def load_rows():
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class TestFrozenPolicyArtifact(unittest.TestCase):
    def test_checksum_layout_and_export_contract_are_exact(self):
        matching_hashes = []
        for line in SHA_MANIFEST.read_text(encoding="utf-8").splitlines():
            match = re.fullmatch(r"([0-9a-fA-F]{64})\s+[ *](.+)", line.strip())
            if match and Path(match.group(2)).name == "policy_rom.mem":
                matching_hashes.append(match.group(1).lower())
        self.assertEqual(matching_hashes, [digest(POLICY_MEM)])
        layout = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))["policy_rom"]
        self.assertEqual(layout["depth"], 256)
        self.assertEqual(layout["useful_width_bits"], 2)
        self.assertEqual(layout["file_hex_digits_per_word"], 1)
        self.assertEqual(layout["address_order"], "state_id_0_to_255")
        manifest = json.loads(EXPORT_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["policy_entry_count"], 256)
        self.assertTrue(manifest["policy_roundtrip_match"])
        self.assertEqual(manifest["q_quantization"]["policy_argmax_mismatch_count"], 0)

    def test_memory_is_exact_frozen_policy_and_exercises_all_actions(self):
        words = read_policy()
        _q_table, frozen_policy, _codebook = validate_inputs()
        self.assertEqual(words, tuple(frozen_policy))
        self.assertEqual(set(words), {0, 1, 2, 3})
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["policy_rom"]["deployment_artifact"], "results/rl/p3_export/policy_rom.mem")
        self.assertEqual(contract["policy_rom"]["depth"], 256)
        self.assertEqual(contract["policy_rom"]["action_width_bits"], 2)
        self.assertEqual(contract["policy_rom"]["read_latency_cycles"], 1)


class TestPolicyVectors(unittest.TestCase):
    def test_all_256_addresses_have_exact_action_agreement(self):
        policy = read_policy()
        rows = [row for row in load_rows() if row["category"] == "all_256_states"]
        self.assertEqual(len(rows), 256)
        self.assertEqual({int(row["state_id"]) for row in rows}, set(range(256)))
        for row in rows:
            state_id = int(row["state_id"])
            self.assertEqual(int(row["expected_valid"]), 1)
            self.assertEqual(int(row["expected_proposed_action"]), policy[state_id])

    def test_reset_enable_hold_and_post_reset_read_are_deterministic(self):
        policy = read_policy()
        rows = load_rows()
        self.assertEqual(len(rows), 260)
        held_action = 0
        for expected_case, row in enumerate(rows):
            self.assertEqual(int(row["case_id"]), expected_case)
            rst = int(row["rst"])
            en = int(row["en"])
            state_id = int(row["state_id"])
            if rst:
                held_action = 0
                expected_valid = 0
            elif en:
                held_action = policy[state_id]
                expected_valid = 1
            else:
                expected_valid = 0
            self.assertEqual(int(row["expected_valid"]), expected_valid)
            self.assertEqual(int(row["expected_proposed_action"]), held_action)
        self.assertEqual(sum(row["category"] == "reset" for row in rows), 2)
        self.assertEqual(sum(row["category"] == "enable_hold" for row in rows), 1)
        self.assertEqual(sum(row["category"] == "post_reset_read" for row in rows), 1)

    def test_numeric_rtl_vectors_match_reviewable_csv(self):
        rows = load_rows()
        lines = RTL_VECTOR_PATH.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), len(rows))
        columns = (
            "case_id",
            "rst",
            "en",
            "state_id",
            "expected_valid",
            "expected_proposed_action",
        )
        for row, line in zip(rows, lines):
            self.assertEqual(tuple(map(int, line.split())), tuple(int(row[name]) for name in columns))

    def test_generator_is_byte_reproducible(self):
        spec = importlib.util.spec_from_file_location("p4_policy_generator", GENERATOR_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        policy = module.read_frozen_policy()
        rows = module.build_vectors(policy)
        with tempfile.TemporaryDirectory() as directory:
            csv_output = Path(directory) / "vectors.csv"
            rtl_output = Path(directory) / "vectors.txt"
            module.write_vectors(rows, csv_output, rtl_output)
            self.assertEqual(csv_output.read_bytes(), CSV_PATH.read_bytes())
            self.assertEqual(rtl_output.read_bytes(), RTL_VECTOR_PATH.read_bytes())


class TestPolicyRomRTL(unittest.TestCase):
    def test_rtl_is_registered_verilog_2001_and_reads_frozen_memory(self):
        text = RTL_PATH.read_text(encoding="utf-8")
        required = (
            "module rl_policy_rom",
            'parameter MEM_FILE = "results/rl/p3_export/policy_rom.mem"',
            "reg [1:0] policy_mem [0:255];",
            "$readmemh(MEM_FILE, policy_mem);",
            "always @(posedge clk)",
            "valid           <= 1'b0;",
            "proposed_action <= 2'd0;",
            "valid <= en;",
            "proposed_action <= policy_mem[state_id];",
        )
        for token in required:
            self.assertIn(token, text)
        for forbidden in ("always_ff", "always_comb", "logic ", "typedef", "package ", "interface "):
            self.assertNotIn(forbidden, text)
        self.assertEqual(text.count("initial begin"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
