"""Independent P4 Step 3 contract tests for rl_state_encoder.v and its vectors."""

import csv
from decimal import Decimal, ROUND_HALF_UP
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "rl/config/p4_rtl_contract_v1.json"
RTL_PATH = REPO_ROOT / "rtl/rl/rl_state_encoder.v"
GENERATOR_PATH = REPO_ROOT / "sim/rl/p4_generate_state_encoder_vectors.py"
CSV_PATH = REPO_ROOT / "sim/rl/p4_state_encoder_vectors.csv"
RTL_VECTOR_PATH = REPO_ROOT / "sim/rl/p4_state_encoder_vectors.txt"

FEATURE_ORDER = (
    "min_key_occupancy",
    "bottleneck_fidelity",
    "offered_request_load",
    "utilization_imbalance",
)
PYTHON_THRESHOLDS = {
    "min_key_occupancy": ("0.25", "0.5", "0.75"),
    "bottleneck_fidelity": ("0.9", "0.93", "0.96"),
    "offered_request_load": ("0.25", "0.5", "0.75"),
    "utilization_imbalance": ("0.125", "0.25", "0.5"),
}


def unorm16(value):
    return int(
        (Decimal(value) * Decimal(65535)).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )


INDEPENDENT_CODES = {
    name: tuple(unorm16(value) for value in values)
    for name, values in PYTHON_THRESHOLDS.items()
}


def independent_encode(values):
    state_id = 0
    for name, value in zip(FEATURE_ORDER, values):
        state_id = state_id * 4 + sum(value >= code for code in INDEPENDENT_CODES[name])
    return state_id


def load_rows():
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class TestFrozenBoundary(unittest.TestCase):
    def test_contract_thresholds_are_independently_rederived(self):
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        state = contract["state_interface"]
        self.assertEqual(tuple(state["feature_order_msb_to_lsb"]), FEATURE_ORDER)
        self.assertEqual(state["comparison_rule"], "bin increments when encoded_value >= threshold_code")
        for name in FEATURE_ORDER:
            self.assertEqual(
                tuple(state["features"][name]["threshold_codes"]),
                INDEPENDENT_CODES[name],
            )

    def test_all_256_state_categories_are_explicit_and_exact(self):
        rows = [row for row in load_rows() if row["category"] == "all_256_states"]
        self.assertEqual(len(rows), 256)
        observed = set()
        for row in rows:
            values = tuple(
                int(row[column])
                for column in (
                    "min_key_occupancy_u16",
                    "bottleneck_fidelity_u16",
                    "offered_request_load_u16",
                    "utilization_imbalance_u16",
                )
            )
            expected = independent_encode(values)
            self.assertEqual(int(row["expected_state_id"]), expected)
            observed.add(expected)
        self.assertEqual(observed, set(range(256)))

    def test_all_36_threshold_edge_vectors_are_exact(self):
        rows = load_rows()
        categories = {
            name: [row for row in rows if row["category"] == name]
            for name in ("threshold_below", "threshold_equal", "threshold_above")
        }
        self.assertEqual({name: len(values) for name, values in categories.items()}, {
            "threshold_below": 12,
            "threshold_equal": 12,
            "threshold_above": 12,
        })
        for row in sum(categories.values(), []):
            values = tuple(
                int(row[column])
                for column in (
                    "min_key_occupancy_u16",
                    "bottleneck_fidelity_u16",
                    "offered_request_load_u16",
                    "utilization_imbalance_u16",
                )
            )
            self.assertEqual(int(row["expected_state_id"]), independent_encode(values))


class TestVectorSequence(unittest.TestCase):
    def test_reset_enable_endpoints_and_registered_sequence(self):
        rows = load_rows()
        self.assertEqual(len(rows), 297)
        held_state = 0
        for expected_case, row in enumerate(rows):
            self.assertEqual(int(row["case_id"]), expected_case)
            rst = int(row["rst"])
            en = int(row["en"])
            values = tuple(
                int(row[column])
                for column in (
                    "min_key_occupancy_u16",
                    "bottleneck_fidelity_u16",
                    "offered_request_load_u16",
                    "utilization_imbalance_u16",
                )
            )
            if rst:
                held_state = 0
                expected_valid = 0
            elif en:
                held_state = independent_encode(values)
                expected_valid = 1
            else:
                expected_valid = 0
            self.assertEqual(int(row["expected_valid"]), expected_valid)
            self.assertEqual(int(row["expected_state_id"]), held_state)
        self.assertEqual(sum(row["category"] == "reset" for row in rows), 2)
        self.assertEqual(sum(row["category"] == "encoded_clip_low" for row in rows), 1)
        self.assertEqual(sum(row["category"] == "encoded_clip_high" for row in rows), 1)
        self.assertEqual(sum(row["category"] == "enable_hold" for row in rows), 1)

    def test_numeric_rtl_vectors_match_the_reviewable_csv(self):
        rows = load_rows()
        numeric_lines = RTL_VECTOR_PATH.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(numeric_lines), len(rows))
        columns = (
            "case_id",
            "rst",
            "en",
            "min_key_occupancy_u16",
            "bottleneck_fidelity_u16",
            "offered_request_load_u16",
            "utilization_imbalance_u16",
            "expected_valid",
            "expected_state_id",
        )
        for row, line in zip(rows, numeric_lines):
            self.assertEqual(tuple(map(int, line.split())), tuple(int(row[name]) for name in columns))

    def test_generator_is_byte_reproducible(self):
        spec = importlib.util.spec_from_file_location("p4_state_vector_generator", GENERATOR_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        rows = module.build_vectors(contract)
        with tempfile.TemporaryDirectory() as directory:
            csv_output = Path(directory) / "vectors.csv"
            rtl_output = Path(directory) / "vectors.txt"
            module.write_vectors(rows, csv_output, rtl_output)
            self.assertEqual(csv_output.read_bytes(), CSV_PATH.read_bytes())
            self.assertEqual(rtl_output.read_bytes(), RTL_VECTOR_PATH.read_bytes())


class TestVerilogBoundary(unittest.TestCase):
    def test_rtl_is_verilog_2001_and_contains_the_exact_frozen_boundary(self):
        text = RTL_PATH.read_text(encoding="utf-8")
        required = (
            "module rl_state_encoder",
            "always @(posedge clk)",
            "if (rst)",
            "valid    <= 1'b0;",
            "state_id <= 8'd0;",
            "valid <= en;",
            "16'd8192",
            "16'd16384",
            "16'd32768",
            "16'd49151",
            "16'd58982",
            "16'd60948",
            "16'd62914",
        )
        for token in required:
            self.assertIn(token, text)
        for forbidden in ("always_ff", "always_comb", "logic ", "typedef", "package ", "interface "):
            self.assertNotIn(forbidden, text)
        self.assertNotIn("initial begin", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
