#!/usr/bin/env python3
"""Parse the controlled P4 XST/NGDBuild evidence without making timing claims."""

import argparse
import hashlib
import json
import re
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(text: str, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return int(match.group(1).replace(",", ""))
    return None


def parse(report: Path, ngdbuild_log: Path, ngc: Path, ngd: Path, source_checkpoint: str):
    xst = report.read_text(errors="replace")
    ngd_log = ngdbuild_log.read_text(errors="replace")
    if not re.search(r"Release 14\.7.*xst", xst, re.IGNORECASE):
        raise ValueError("XST 14.7 release sentinel missing")
    exact_part = re.search(r"xc6slx16-2-csg324", xst, re.IGNORECASE)
    split_part = all(re.search(pattern, xst, re.IGNORECASE) for pattern in (
        r"xc6slx16", r"csg324", r"(?:Target Speed|Speed Grade|Speed)\s*[:=]?\s*-2",
    ))
    if not exact_part and not split_part:
        raise ValueError("exact target part missing from XST report")
    if not re.search(r"rl_controller_synth_top", xst):
        raise ValueError("synthesis top missing from XST report")
    if re.search(r"(?:^|\n)\s*ERROR:(?:Xst|NgdBuild|Pack|Map|Par)", xst + "\n" + ngd_log, re.IGNORECASE):
        raise ValueError("ISE error found in reports")
    if not ngc.is_file() or ngc.stat().st_size == 0:
        raise ValueError("NGC netlist is absent or empty")
    if not ngd.is_file() or ngd.stat().st_size == 0:
        raise ValueError("NGD translated netlist is absent or empty")
    if not re.search(r"NGDBUILD.*(?:completed successfully|done)|Writing NGD file|NGD file.*written", ngd_log, re.IGNORECASE):
        raise ValueError("NGDBuild success sentinel missing")

    period = re.search(r"Minimum period:\s*([0-9.]+)\s*ns", xst, re.IGNORECASE)
    frequency = re.search(r"Maximum Frequency:\s*([0-9.]+)\s*MHz", xst, re.IGNORECASE)
    xst_errors = number(xst, (r"Number of errors:\s*([0-9,]+)",))
    xst_warnings = number(xst, (r"Number of warnings:\s*([0-9,]+)",))
    if xst_errors not in (None, 0):
        raise ValueError("XST error count is nonzero")

    resources = {
        "slice_registers": number(xst, (r"Number of Slice Registers:\s*([0-9,]+)",)),
        "slice_luts": number(xst, (r"Number of Slice LUTs:\s*([0-9,]+)",)),
        "occupied_slices": number(xst, (r"Number of occupied Slices:\s*([0-9,]+)",)),
        "block_ram_fifo": number(xst, (r"Number of Block RAM/FIFO:\s*([0-9,]+)", r"Number of RAMB16BWERs:\s*([0-9,]+)")),
        "dsp48a1": number(xst, (r"Number of DSP48A1s:\s*([0-9,]+)",)),
        "bufg_bufgctrl": number(xst, (r"Number of BUFG/BUFGCTRLs:\s*([0-9,]+)",)),
    }
    return {
        "schema_version": 1,
        "phase": "P4",
        "step": "P4_STEP_9_ISE_SYNTHESIS",
        "decision": "PASS_PENDING_REVIEW",
        "source_checkpoint": source_checkpoint,
        "target_board": "Digilent Nexys 3",
        "target_part": "xc6slx16-2-csg324",
        "tool": "Xilinx ISE XST",
        "tool_release": "14.7",
        "top": "rl_controller_synth_top",
        "rtl_standard": "Verilog-2001",
        "xst_error_count": 0 if xst_errors is None else xst_errors,
        "xst_warning_count": xst_warnings,
        "resources": resources,
        "xst_minimum_period_ns_estimate": float(period.group(1)) if period else None,
        "xst_maximum_frequency_mhz_estimate": float(frequency.group(1)) if frequency else None,
        "timing_scope": "XST post-synthesis estimate only; no Map/PAR/TRCE timing closure claim",
        "ngc_valid": True,
        "ngd_translation_valid": True,
        "ngc_size_bytes": ngc.stat().st_size,
        "ngd_size_bytes": ngd.stat().st_size,
        "ngc_sha256": digest(ngc),
        "ngd_sha256": digest(ngd),
        "map_performed": False,
        "par_performed": False,
        "trce_signoff_performed": False,
        "bitgen_performed": False,
        "board_programming_performed": False,
        "eeprom_access_performed": False,
        "rtl_changed": False,
        "policy_or_profile_changed": False,
        "training_changed": False,
        "policy_rom_deployed": True,
        "q_table_role": "audit_only",
        "runtime_argmax_deployed": False,
        "q_update_implemented": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--xst-report", type=Path, required=True)
    parser.add_argument("--ngdbuild-log", type=Path, required=True)
    parser.add_argument("--ngc", type=Path, required=True)
    parser.add_argument("--ngd", type=Path, required=True)
    parser.add_argument("--source-checkpoint", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = parse(args.xst_report, args.ngdbuild_log, args.ngc, args.ngd, args.source_checkpoint)
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(f"P4_ISE_NGC_BYTES={record['ngc_size_bytes']}")
    print(f"P4_ISE_NGD_BYTES={record['ngd_size_bytes']}")
    print(f"P4_ISE_XST_ERRORS={record['xst_error_count']}")
    print("P4_ISE_TIMING_SCOPE=XST_ESTIMATE_ONLY")


if __name__ == "__main__":
    main()
