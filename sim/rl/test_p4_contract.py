"""P4 Step 2 contract-freeze validation; no RTL or synthesis is performed."""

from decimal import Decimal, ROUND_HALF_UP
from itertools import product
import hashlib
import json
from pathlib import Path
import unittest

from rl.dwell_controller import MinimumDwellController, validate_policy
from rl.mdp_contract import CONTRACT as MDP_CONTRACT, decode_state_id, feature_bin
from rl.p3_export import decode_profile, encode_profile, validate_inputs


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "rl/config/p4_rtl_contract_v1.json"
SCHEMA_PATH = REPO_ROOT / "sim/rl/p4_golden_vector_schema.json"
LAYOUT_PATH = REPO_ROOT / "results/rl/p3_export/rom_layout.json"
MANIFEST_PATH = REPO_ROOT / "results/rl/p3_export/export_manifest.json"
POLICY_MEM = REPO_ROOT / "results/rl/p3_export/policy_rom.mem"
PROFILE_MEM = REPO_ROOT / "results/rl/p3_export/profile_rom.mem"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def unorm16(value):
    clipped = min(Decimal("1"), max(Decimal("0"), Decimal(str(value))))
    return int((clipped * Decimal(65535)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def packed_state(bins):
    result = 0
    for value in bins:
        result = result * 4 + value
    return result


def encoded_bin(value, thresholds):
    return sum(value >= threshold for threshold in thresholds)


def saturating_dwell_timeline(proposed_actions, minimum=3):
    current = None
    dwell = 0
    output = []
    for proposed in proposed_actions:
        if current is None:
            current, dwell = proposed, 1
        elif proposed != current and dwell >= minimum:
            current, dwell = proposed, 1
        else:
            dwell = min(minimum, dwell + 1)
        output.append((current, dwell))
    return output


class TestStateContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_json(CONTRACT_PATH)

    def test_source_checkpoint_and_state_shape(self):
        self.assertEqual(
            self.contract["source_checkpoint"],
            "cdfeda3f5f2fca586546ef6e362ac451512d75bc",
        )
        state = self.contract["state_interface"]
        self.assertEqual(state["representation"], "UNORM16")
        self.assertEqual(state["input_width_bits_per_feature"], 16)
        self.assertEqual(state["state_count"], 256)

    def test_python_thresholds_and_unorm_codes_are_exactly_derived(self):
        state = self.contract["state_interface"]
        for feature_name in MDP_CONTRACT["state"]["feature_order"]:
            source = MDP_CONTRACT["state"]["features"][feature_name]["thresholds"]
            frozen = state["features"][feature_name]
            self.assertEqual(frozen["python_thresholds"], source)
            self.assertEqual(
                frozen["threshold_codes"],
                [unorm16(value) for value in source],
            )
            for expected_bin, threshold in enumerate(source, 1):
                self.assertEqual(feature_bin(feature_name, threshold), expected_bin)

    def test_encoded_below_equal_above_rule(self):
        for feature in self.contract["state_interface"]["features"].values():
            thresholds = feature["threshold_codes"]
            for expected_bin, threshold in enumerate(thresholds, 1):
                self.assertEqual(encoded_bin(threshold - 1, thresholds), expected_bin - 1)
                self.assertEqual(encoded_bin(threshold, thresholds), expected_bin)
                if threshold < 65535:
                    self.assertEqual(encoded_bin(threshold + 1, thresholds), expected_bin)

    def test_all_state_ids_pack_and_decode_exactly(self):
        observed = set()
        for bins in product(range(4), repeat=4):
            state_id = packed_state(bins)
            observed.add(state_id)
            self.assertEqual(decode_state_id(state_id), bins)
        self.assertEqual(observed, set(range(256)))


class TestRomAndProfileContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_json(CONTRACT_PATH)
        cls.layout = load_json(LAYOUT_PATH)
        cls.manifest = load_json(MANIFEST_PATH)
        cls.q_table, cls.policy, cls.codebook = validate_inputs()

    def test_policy_rom_is_exact_frozen_policy(self):
        words = tuple(int(value, 16) for value in POLICY_MEM.read_text().splitlines())
        self.assertEqual(words, self.policy)
        self.assertEqual(set(words), {0, 1, 2, 3})
        self.assertEqual(self.contract["policy_rom"]["depth"], 256)
        self.assertEqual(self.contract["policy_rom"]["action_width_bits"], 2)

    def test_profile_rom_is_four_18_bit_entries_totaling_72_bits(self):
        words = tuple(int(value, 16) for value in PROFILE_MEM.read_text().splitlines())
        expected = tuple(encode_profile(profile) for profile in self.codebook["profiles"])
        self.assertEqual(words, expected)
        self.assertEqual(self.contract["profile_rom"]["payload_width_bits_per_profile"], 18)
        self.assertEqual(self.contract["profile_rom"]["complete_rom_payload_bits"], 72)
        self.assertEqual(len(words) * 18, 72)
        for word, profile in zip(words, self.codebook["profiles"]):
            alphas, ratios = decode_profile(word)
            self.assertEqual(alphas, tuple(int(round(float(v) * 2)) for v in profile["alphas"]))
            self.assertEqual(ratios, tuple(int(v) for v in profile["lambda_tch_hw_ratio"]))

    def test_policy_rom_is_deployed_and_q_table_is_audit_only(self):
        self.assertEqual(self.contract["q_table"]["deployment_role"], "audit_only")
        self.assertFalse(self.contract["q_table"]["deployed_in_p4"])
        self.assertEqual(self.layout["q_table"]["format_name"], "Q8.7")
        self.assertEqual(self.manifest["q_quantization"]["policy_argmax_mismatch_count"], 0)


class TestDwellContract(unittest.TestCase):
    def test_saturating_hardware_count_preserves_python_action_timeline(self):
        policy = [0] * 256
        policy[:4] = [0, 1, 2, 3]
        policy = validate_policy(policy)
        for proposed in product(range(4), repeat=6):
            controller = MinimumDwellController(policy, 3)
            python_actions = [controller.choose_action(action) for action in proposed]
            hardware = saturating_dwell_timeline(proposed, 3)
            self.assertEqual(python_actions, [action for action, _count in hardware])

    def test_reset_removes_dwell_history(self):
        policy = [0] * 256
        policy[1] = 1
        controller = MinimumDwellController(policy, 3)
        self.assertEqual([controller.choose_action(v) for v in (0, 1, 1)], [0, 0, 0])
        controller.reset()
        self.assertEqual(controller.choose_action(1), 1)


class TestHandshakeSchemaAndClaims(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_json(CONTRACT_PATH)
        cls.schema = load_json(SCHEMA_PATH)

    def test_handshake_and_exception_rules_are_complete(self):
        timing = self.contract["module_timing"]
        for key in ("reset", "done", "output_valid", "ready", "busy", "stall"):
            self.assertIn(key, timing)
        exceptions = self.contract["exception_behavior"]
        for key in ("input_valid_low", "no_path", "start_while_busy"):
            self.assertIn(key, exceptions)

    def test_module_port_widths_are_frozen(self):
        ports = self.contract["module_ports"]
        self.assertEqual(ports["rl_state_encoder"]["outputs"]["state_id"], 8)
        self.assertEqual(ports["rl_policy_rom"]["outputs"]["proposed_action"], 2)
        self.assertEqual(ports["rl_profile_rom"]["outputs"]["profile_payload"], 18)
        controller = ports["rl_controller"]
        self.assertEqual(controller["inputs"]["min_key_occupancy_u16"], 16)
        self.assertEqual(controller["outputs"]["dwell_count_sat"], 2)

    def test_golden_schema_has_unique_columns_and_required_categories(self):
        columns = self.schema["columns"]
        categories = self.schema["required_categories"]
        self.assertEqual(len(columns), len(set(columns)))
        self.assertIn("all_256_states", categories)
        self.assertIn("threshold_equal", categories)
        self.assertIn("dwell_switch", categories)
        self.assertIn("start_while_busy", categories)
        self.assertEqual(self.schema["comparison"]["unexplained_mismatches_allowed"], 0)

    def test_claim_firewall_is_all_false(self):
        firewall = self.contract["claim_firewall"]
        self.assertTrue(firewall)
        self.assertTrue(all(value is False for value in firewall.values()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
