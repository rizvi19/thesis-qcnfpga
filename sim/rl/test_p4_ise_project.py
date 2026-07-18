"""Independent contract tests for the P4 Step 9 ISE synthesis project."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / "fpga/ise_nexys3/p4_controller/rl_controller_synth_top.v"
PROJECT = ROOT / "fpga/ise_nexys3/p4_controller/controller.prj"
XST = ROOT / "fpga/ise_nexys3/p4_controller/controller.xst"
STATUS = ROOT / "docs/rl/p4_step9_status.md"
CONTRACT = ROOT / "rl/config/p4_rtl_contract_v1.json"
PARSER = ROOT / "sim/rl/p4_parse_xst_report.py"


class TestTransparentSynthesisTop(unittest.TestCase):
    def test_wrapper_exposes_every_frozen_controller_port(self):
        contract = json.loads(CONTRACT.read_text())["module_ports"]["rl_controller"]
        text = WRAPPER.read_text()
        for name in (*contract["inputs"], *contract["outputs"]):
            self.assertIn(name, text)
            self.assertEqual(text.count(f".{name}({name})"), 1)

    def test_wrapper_adds_no_behavior_or_state(self):
        text = WRAPPER.read_text()
        self.assertEqual(text.count("rl_controller controller_i"), 1)
        for forbidden in ("always", "initial", "reg ", "assign ", "readmem", "q_update", "argmax"):
            self.assertNotIn(forbidden, text)


class TestISEProjectContract(unittest.TestCase):
    def test_project_has_exact_reviewed_source_order(self):
        self.assertEqual(PROJECT.read_text().splitlines(), [
            'verilog work "rtl/rl/rl_state_encoder.v"',
            'verilog work "rtl/rl/rl_policy_rom.v"',
            'verilog work "rtl/rl/rl_profile_rom.v"',
            'verilog work "rtl/rl/rl_controller.v"',
            'verilog work "fpga/ise_nexys3/p4_controller/rl_controller_synth_top.v"',
        ])

    def test_xst_targets_exact_part_top_and_supported_spartan6_flow(self):
        text = XST.read_text()
        for phrase in ("-ifmt mixed", "-p xc6slx16-2-csg324", "-top rl_controller_synth_top", "-ofmt NGC", "-keep_hierarchy YES"):
            self.assertIn(phrase, text)
        for forbidden in ("-verilog2001", "xc7", "map ", "par ", "trce ", "bitgen", ".ucf"):
            self.assertNotIn(forbidden, text.lower())

    def test_status_preserves_synthesis_and_claim_firewalls(self):
        text = STATUS.read_text()
        for phrase in ("XST", "NGDBuild", "not post-PAR timing closure", "no UCF", "audit-only", "board programming", "EEPROM"):
            self.assertIn(phrase, text)


class TestReportParser(unittest.TestCase):
    def test_parser_accepts_synthetic_zero_error_evidence(self):
        spec = importlib.util.spec_from_file_location("p4_xst_parser", PARSER)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); report=root/"xst.syr"; ngdlog=root/"ngdbuild.log"; ngc=root/"a.ngc"; ngd=root/"a.ngd"
            report.write_text("Release 14.7 - xst P.20131013\nPart xc6slx16-2-csg324\nTop rl_controller_synth_top\nNumber of errors: 0\nNumber of Slice Registers: 12\nNumber of Slice LUTs: 34\nMinimum period: 5.000ns (Maximum Frequency: 200.000MHz)\n")
            ngdlog.write_text("NGDBUILD completed successfully. Writing NGD file.\n"); ngc.write_bytes(b"ngc"); ngd.write_bytes(b"ngd")
            result=module.parse(report,ngdlog,ngc,ngd,"checkpoint")
            self.assertEqual(result["decision"],"PASS_PENDING_REVIEW")
            self.assertEqual(result["resources"]["slice_registers"],12)
            self.assertEqual(result["resources"]["slice_luts"],34)
            self.assertEqual(result["xst_maximum_frequency_mhz_estimate"],200.0)
            self.assertFalse(result["map_performed"])
            self.assertFalse(result["board_programming_performed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
