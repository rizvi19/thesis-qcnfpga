#!/usr/bin/env python3
"""Executable P5 Step 2 contract consistency gate; standard library only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "rl/config/p5_qflow_mini_contract_v1.json"
SCHEMA_PATH = ROOT / "sim/rl/p5_qflow_mini_vector_schema.json"
DOCS = [
    ROOT / "docs/rl/p5_qflow_mini_contract.md",
    ROOT / "docs/rl/p5_board_interface_contract.md",
    ROOT / "docs/rl/p5_verification_contract.md",
    ROOT / "docs/rl/p5_step2_status.md",
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def ring_path(src: int, dst: int, delta: int):
    path = [src]
    node = src
    while node != dst:
        node = (node + delta) % 6
        path.append(node)
    return tuple(path)


class P5ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load(CONTRACT_PATH)
        cls.schema = load(SCHEMA_PATH)

    def test_source_and_scope(self):
        c = self.contract
        self.assertEqual(c["source_checkpoint"], "2dba73ea36e6cd35b43cf3d06cbf6e774a6e429d")
        self.assertEqual(c["branch"], "rl-nexys3-adaptive")
        prohibited = set(c["scope"]["prohibited"])
        required = {"rtl", "ucf", "ise_activation", "xst", "ngdbuild", "map", "par", "trce", "bitgen", "live_board_enumeration", "uart_access", "board_programming", "eeprom_access", "stage", "commit", "push"}
        self.assertTrue(required <= prohibited)
        self.assertTrue(all(value is False for value in c["claim_firewall"].values()))

    def test_authority_hashes(self):
        for rel, expected in self.contract["authority_sha256"].items():
            path = ROOT / rel
            self.assertTrue(path.is_file(), rel)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected, rel)

    def test_topology_and_paths(self):
        t = self.contract["topology"]
        self.assertEqual(t["nodes"], list(range(6)))
        self.assertEqual(len(t["directed_edges"]), 12)
        self.assertEqual(len({tuple(edge) for edge in t["directed_edges"]}), 12)
        self.assertEqual(t["candidate_slot_count"], 4)
        self.assertEqual([x["valid"] for x in t["candidate_slots"]], [True, True, False, False])
        edges = {tuple(edge) for edge in t["directed_edges"]}
        for src in range(6):
            for dst in range(6):
                if src == dst:
                    continue
                for delta in (1, -1):
                    path = ring_path(src, dst, delta)
                    self.assertEqual(path[0], src)
                    self.assertEqual(path[-1], dst)
                    self.assertEqual(len(path), len(set(path)))
                    self.assertTrue(all(edge in edges for edge in zip(path, path[1:])))

    def test_numeric_contract(self):
        f = self.contract["fixed_point"]
        self.assertEqual(f["fidelity_qber"]["scale"], 65535)
        self.assertEqual(f["weight"]["infinity"], 0xFFFFFFFF)
        self.assertEqual(f["weight"]["max_finite"], 0xFFFFFFFE)
        self.assertEqual(self.contract["candidate_evaluator"]["fidelity_floor_unorm16"], 58982)
        self.assertEqual(self.contract["fdpe_mini"]["lut_depth"], 256)
        self.assertEqual(self.contract["fdpe_mini"]["interpolation_fraction_denominator"], 128)

    def test_p4_handoff(self):
        h4 = self.contract["policy_shell"]["h4"]
        self.assertEqual(h4["state_count"], 256)
        self.assertEqual(h4["action_count"], 4)
        self.assertEqual(h4["minimum_dwell_decisions"], 3)
        self.assertEqual(h4["valid_controller_latency_cycles"], 3)
        self.assertEqual(h4["profile_payloads_hex"], ["13329", "1B516", "14399", "0A2A5"])
        self.assertFalse(h4["runtime_argmax"])
        self.assertFalse(h4["q_update"])
        self.assertFalse(h4["online_learning"])

    def test_handshake_and_uart(self):
        hs = self.contract["handshake"]
        self.assertIn("start_and_ready_and_input_valid", hs["accept"])
        self.assertIn("N_done_minus_N_accept", hs["latency_cycles"])
        uart = self.contract["uart"]
        self.assertEqual(uart["result_prefix"], "QF5R")
        self.assertEqual(uart["record_version"], 1)
        self.assertEqual(set(map(int, uart["status_codes"].keys())), {0,1,2,3,4})
        self.assertEqual(uart["baud_and_pins"], "deferred_to_B1_review")

    def test_fallback_and_milestones(self):
        self.assertEqual(self.contract["milestones"], ["B1_clock_reset_display_uart", "B2_fdpe_mini", "B3_skag_mini", "B4_candidate_evaluator", "B5_policy_shell_H0_H4", "B6_internal_latency_counter"])
        self.assertEqual(self.contract["fallback_order"][-1], "reduce_numeric_widths_with_revalidation")

    def test_vector_schema(self):
        s = self.schema
        self.assertEqual(s["contract"], "rl/config/p5_qflow_mini_contract_v1.json")
        self.assertFalse(s["step2_generates_vectors"])
        names = [item["name"] for item in s["common_columns"]]
        self.assertEqual(len(names), len(set(names)))
        for required in ("test_id", "policy_id", "state_id", "profile_id", "selected_path", "score", "bottleneck_fidelity", "cycles", "status"):
            self.assertIn(required, names)
        self.assertEqual(s["required_coverage"]["ordered_endpoint_pairs"], 30)
        self.assertEqual(s["required_coverage"]["reserved_candidate_slots"], [2,3])

    def test_document_claim_firewalls(self):
        for path in DOCS:
            self.assertTrue(path.is_file())
            text = path.read_text(encoding="utf-8")
            self.assertIn("EEPROM", text)
        status = DOCS[-1].read_text(encoding="utf-8")
        self.assertIn("AWAITING_HUMAN_REVIEW", status)
        self.assertIn("creates no RTL or UCF", status)


if __name__ == "__main__":
    unittest.main(verbosity=2)
