#!/usr/bin/env python3
"""Validate the controlled P5 B1 offline ISE implementation evidence."""

import argparse
import hashlib
import json
import re
from pathlib import Path


EXPECTED_PART = "xc6slx16-2-csg324"
EXPECTED_TOP = "p5_b1_top"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def required_file(build: Path, name: str) -> Path:
    path = build / name
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"required build artifact absent or empty: {name}")
    return path


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def no_ise_errors(name: str, text: str) -> None:
    if re.search(r"(?:^|\n)\s*ERROR:[A-Za-z]", text, re.IGNORECASE):
        raise ValueError(f"ISE error found in {name}")


def integer(text: str, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return int(match.group(1).replace(",", ""))
    return None


def decimal(text: str, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return float(match.group(1))
    return None


def validate_contract(repo: Path) -> None:
    project = read(repo / "fpga/ise_nexys3/p5_b1/p5_b1.prj").splitlines()
    expected = [
        'verilog work "p5_b1_uart_tx.v"',
        'verilog work "p5_b1_sevenseg.v"',
        'verilog work "p5_b1_top.v"',
    ]
    if project != expected:
        raise ValueError("ISE project source order differs from the frozen contract")

    xst = read(repo / "fpga/ise_nexys3/p5_b1/p5_b1.xst")
    if f"-p {EXPECTED_PART}" not in xst or f"-top {EXPECTED_TOP}" not in xst:
        raise ValueError("XST part/top contract missing")
    if "-verilog2001" in xst.lower():
        raise ValueError("unsupported Spartan-6 XST -verilog2001 option present")

    ucf = read(repo / "constraints/nexys3/p5_b1_io_sanity.ucf")
    if 'TIMESPEC "TS_P5_B1_CLK" = PERIOD "P5_B1_CLK" 10 ns HIGH 50%;' not in ucf:
        raise ValueError("exact 10 ns UCF clock constraint missing")
    if len(re.findall(r'\bLOC\s*=\s*"[A-Z][0-9]+"', ucf)) != 17:
        raise ValueError("expected 17 LOC constraints")


def parse(build: Path, repo: Path, source_checkpoint: str):
    validate_contract(repo)

    names = [
        "xst.log",
        "p5_b1.syr",
        "ngdbuild.log",
        "map.log",
        "p5_b1_map.mrp",
        "par.log",
        "p5_b1_routed.par",
        "trce.log",
        "p5_b1.twr",
        "bitgen.log",
        "p5_b1.bit",
        "p5_b1.ngc",
        "p5_b1.ngd",
        "p5_b1.pcf",
        "p5_b1_map.ncd",
        "p5_b1_routed.ncd",
    ]
    files = {name: required_file(build, name) for name in names}

    texts = {
        name: read(path)
        for name, path in files.items()
        if path.suffix not in {".bit", ".ngc", ".ngd", ".ncd"}
    }
    for name, value in texts.items():
        no_ise_errors(name, value)

    xst = texts["p5_b1.syr"] + "\n" + texts["xst.log"]
    ngd = texts["ngdbuild.log"]
    map_text = texts["map.log"] + "\n" + texts["p5_b1_map.mrp"]
    par_text = texts["par.log"] + "\n" + texts["p5_b1_routed.par"]
    trce = texts["trce.log"] + "\n" + texts["p5_b1.twr"]
    bitgen = texts["bitgen.log"]

    if not re.search(r"Release 14\.7.*xst", xst, re.IGNORECASE):
        raise ValueError("XST 14.7 release sentinel missing")
    exact_part = re.search(EXPECTED_PART, xst, re.IGNORECASE)
    split_part = all(re.search(pattern, xst, re.IGNORECASE) for pattern in (
        r"xc6slx16", r"csg324", r"(?:Target Speed|Speed Grade|Speed)\s*[:=]?\s*-2",
    ))
    if not exact_part and not split_part:
        raise ValueError("exact target part missing from XST report")
    if not re.search(EXPECTED_TOP, xst):
        raise ValueError("synthesis top missing from XST report")

    xst_errors = integer(xst, (r"Number of errors:\s*([0-9,]+)",))
    if xst_errors not in (None, 0):
        raise ValueError("XST error count is nonzero")
    if not re.search(r"NGDBUILD.*(?:completed successfully|done)|Writing NGD file|NGD file.*written", ngd, re.IGNORECASE):
        raise ValueError("NGDBuild success sentinel missing")
    if not re.search(r"Release 14\.7.*map", map_text, re.IGNORECASE):
        raise ValueError("Map 14.7 release sentinel missing")
    if not re.search(r"Release 14\.7.*par", par_text, re.IGNORECASE):
        raise ValueError("PAR 14.7 release sentinel missing")
    if not re.search(r"All signals are completely routed", par_text, re.IGNORECASE):
        raise ValueError("complete routing sentinel missing")

    timing_score = integer(par_text, (r"Timing Score:\s*([0-9,]+)",))
    if timing_score != 0:
        raise ValueError("PAR timing score is not zero")
    if not re.search(r"TS_P5_B1_CLK|P5_B1_CLK", trce, re.IGNORECASE):
        raise ValueError("named B1 clock constraint missing from TRCE report")
    if not re.search(r"10(?:\.0+)?\s*ns", trce, re.IGNORECASE):
        raise ValueError("10 ns target missing from TRCE report")
    timing_met = bool(re.search(
        r"0\s+timing errors detected|All constraints were met|Timing constraints are met",
        trce,
        re.IGNORECASE,
    ))
    if not timing_met:
        raise ValueError("TRCE does not report zero timing errors/all constraints met")

    if not re.search(r"Release 14\.7.*bitgen", bitgen, re.IGNORECASE):
        raise ValueError("BitGen 14.7 release sentinel missing")

    period = decimal(trce, (
        r"Minimum period:\s*([0-9.]+)\s*ns",
        r"Minimum period\s*=\s*([0-9.]+)\s*ns",
    ))
    frequency = decimal(trce, (
        r"Maximum Frequency:\s*([0-9.]+)\s*MHz",
        r"Maximum frequency\s*=\s*([0-9.]+)\s*MHz",
    ))
    slack = decimal(trce, (r"Slack:\s*([+]?[0-9.]+)\s*ns",))

    resources = {
        "slice_registers": integer(map_text, (r"Slice Registers\s*[:|]\s*([0-9,]+)",)),
        "slice_luts": integer(map_text, (r"Slice LUTs\s*[:|]\s*([0-9,]+)",)),
        "occupied_slices": integer(map_text, (r"occupied Slices\s*[:|]\s*([0-9,]+)",)),
        "bonded_iobs": integer(map_text, (r"bonded IOBs\s*[:|]\s*([0-9,]+)",)),
        "bufg_bufgctrl": integer(map_text, (r"BUFG/BUFGCTRLs\s*[:|]\s*([0-9,]+)",)),
    }

    retained = [
        "toolchain.log",
        "commands.log",
        "xst.log",
        "p5_b1.syr",
        "ngdbuild.log",
        "map.log",
        "p5_b1_map.mrp",
        "par.log",
        "p5_b1_routed.par",
        "trce.log",
        "p5_b1.twr",
        "bitgen.log",
        "p5_b1.bit",
    ]
    retained_files = {name: required_file(build, name) for name in retained}

    return {
        "schema_version": 1,
        "phase": "P5",
        "step": "P5_STEP_3_B1",
        "stage": "B1_STAGE_B_OFFLINE_ISE_IMPLEMENTATION",
        "decision": "PASS_PENDING_ASSISTANT_REVIEW",
        "source_checkpoint": source_checkpoint,
        "target_board": "Digilent Nexys 3",
        "target_part": EXPECTED_PART,
        "top": EXPECTED_TOP,
        "rtl_standard": "Verilog-2001",
        "tool": "Xilinx ISE 14.7 WebPACK",
        "flow": ["XST", "NGDBuild", "Map", "PAR", "TRCE", "BitGen"],
        "clock_target_ns": 10.0,
        "xst_error_count": 0 if xst_errors is None else xst_errors,
        "ngdbuild_error_count": 0,
        "map_error_count": 0,
        "par_error_count": 0,
        "trce_timing_errors": 0,
        "par_timing_score": timing_score,
        "post_par_minimum_period_ns": period,
        "post_par_maximum_frequency_mhz": frequency,
        "reported_slack_ns": slack,
        "resources": resources,
        "bitstream_size_bytes": files["p5_b1.bit"].stat().st_size,
        "bitstream_sha256": digest(files["p5_b1.bit"]),
        "intermediate_artifacts": {
            name: {"bytes": files[name].stat().st_size, "sha256": digest(files[name])}
            for name in ("p5_b1.ngc", "p5_b1.ngd", "p5_b1.pcf", "p5_b1_map.ncd", "p5_b1_routed.ncd")
        },
        "retained_build_evidence": {
            name: {"bytes": path.stat().st_size, "sha256": digest(path)}
            for name, path in retained_files.items()
        },
        "claim_level": "post_par_trce_implemented_timing_for_exact_build_only",
        "board_enumeration_performed": False,
        "uart_device_access_performed": False,
        "board_programming_performed": False,
        "eeprom_access_performed": False,
        "repository_staging_performed": False,
        "repository_commit_performed": False,
        "repository_push_performed": False,
        "b1_complete": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--source-checkpoint", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    record = parse(args.build_dir, args.repo, args.source_checkpoint)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("P5_B1_ISE_XST_ERRORS=0_PASS")
    print("P5_B1_ISE_NGDBUILD_ERRORS=0_PASS")
    print("P5_B1_ISE_MAP_ERRORS=0_PASS")
    print("P5_B1_ISE_PAR_ERRORS=0_PASS")
    print("P5_B1_ISE_PAR_TIMING_SCORE=0_PASS")
    print("P5_B1_ISE_TRCE_TIMING_ERRORS=0_PASS")
    print("P5_B1_ISE_CLOCK_TARGET_10NS=MET_PASS")
    print(f"P5_B1_ISE_BITSTREAM_BYTES={record['bitstream_size_bytes']}_PASS")
    print(f"P5_B1_ISE_BITSTREAM_SHA256={record['bitstream_sha256']}")
    if record["post_par_minimum_period_ns"] is not None:
        print(f"P5_B1_ISE_POST_PAR_MINIMUM_PERIOD_NS={record['post_par_minimum_period_ns']}")
    if record["post_par_maximum_frequency_mhz"] is not None:
        print(f"P5_B1_ISE_POST_PAR_MAXIMUM_FREQUENCY_MHZ={record['post_par_maximum_frequency_mhz']}")
    print("P5_B1_STAGE_B=PASS")


if __name__ == "__main__":
    main()
