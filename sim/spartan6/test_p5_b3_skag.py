#!/usr/bin/env python3
"""Deterministic P5 B3 contract, generator, and RTL simulation gate."""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(command: list[str], timeout: int = 120) -> str:
    completed = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=timeout, check=False)
    require(completed.returncode == 0, "command failed:\n" + completed.stdout)
    return completed.stdout


def main() -> None:
    contract = json.loads((ROOT / "rl/config/p5_qflow_mini_contract_v1.json").read_text())
    skag = contract["skag_mini"]
    require(skag["edge_count"] == 12, "SKAG edge count drift")
    require(skag["weight_equation"] == "alpha1/K + alpha2/F + alpha3/key_rate + alpha4*qber", "SKAG equation drift")
    require(contract["fixed_point"]["rounding"] == "round_to_nearest_half_up", "rounding drift")
    require(contract["fixed_point"]["weight"]["infinity"] == 0xFFFFFFFF, "infinity drift")
    require(contract["policy_shell"]["h4"]["profile_payloads_hex"] == ["13329", "1B516", "14399", "0A2A5"], "profile drift")

    required = [
        ROOT / "tools/generate_p5_b3_skag_vectors.py",
        ROOT / "rtl/spartan6/p5_b3_iterative_divider.v",
        ROOT / "rtl/spartan6/p5_b3_skag.v",
        ROOT / "rtl/spartan6/p5_b3_selftest_top.v",
        ROOT / "rtl/spartan6/p5_b3_board_vectors.vh",
        ROOT / "sim/spartan6/p5_b3_skag_vectors.csv",
        ROOT / "sim/spartan6/p5_b3_skag_vectors.mem",
        ROOT / "sim/spartan6/tb_p5_b3_skag.v",
        ROOT / "sim/spartan6/tb_p5_b3_selftest.v",
    ]
    require(all(path.is_file() for path in required), "P5 B3 source set incomplete")
    text = "\n".join(path.read_text(encoding="utf-8") for path in required if path.suffix in {".v", ".vh"})
    require(not any(token in text for token in ("always_ff", "always_comb", "logic ", "typedef", "interface ")), "non-Verilog-2001 token")

    with tempfile.TemporaryDirectory(prefix="qflow_p5_b3_") as temp_name:
        temp = Path(temp_name)
        csv_out, mem_out, board_out = temp / "vectors.csv", temp / "vectors.mem", temp / "board.vh"
        generated = run([shutil.which("python3") or "python3", str(required[0]),
                         "--csv", str(csv_out), "--mem", str(mem_out), "--board-vh", str(board_out)])
        require("P5_B3_SKAG_VECTOR_COUNT=1056" in generated, generated)
        for actual, expected in ((csv_out, required[5]), (mem_out, required[6]), (board_out, required[4])):
            require(actual.read_bytes() == expected.read_bytes(), f"generator drift: {expected}")
        rows = list(csv.DictReader(required[5].open(encoding="utf-8")))
        require(len(rows) == 1056, "vector count drift")
        require(sum(row["expected_feasible"] == "0" for row in rows) >= 12, "infeasible coverage missing")
        require(any(row["expected_weight_uq16_16_hex"] == "FFFFFFFE" for row in rows), "saturation coverage missing")

        iverilog, vvp = shutil.which("iverilog"), shutil.which("vvp")
        require(iverilog is not None and vvp is not None, "iverilog/vvp unavailable")
        core_exe = temp / "core.out"
        compile_core = run([iverilog, "-g2005", "-Wall", "-s", "tb_p5_b3_skag", "-o", str(core_exe),
                            "rtl/spartan6/p5_b3_iterative_divider.v", "rtl/spartan6/p5_b3_skag.v",
                            "sim/spartan6/tb_p5_b3_skag.v"])
        require("warning" not in compile_core.lower(), compile_core)
        core_output = run([vvp, str(core_exe)], timeout=180)
        require("P5_B3_SKAG_VECTORS=1056_OF_1056_EXACT_PASS" in core_output, core_output)

        board_exe = temp / "board.out"
        compile_board = run([iverilog, "-g2005", "-Wall", "-I", "rtl/spartan6", "-s", "tb_p5_b3_selftest", "-o", str(board_exe),
                             "rtl/spartan6/p5_b3_iterative_divider.v", "rtl/spartan6/p5_b3_skag.v",
                             "rtl/spartan6/p5_b1_sevenseg.v", "rtl/spartan6/p5_b3_selftest_top.v",
                             "sim/spartan6/tb_p5_b3_selftest.v"])
        require("warning" not in compile_board.lower(), compile_board)
        board_output = run([vvp, str(board_exe)])
        require("P5_B3_BOARD_CASES=16_OF_16_EXACT_PASS" in board_output, board_output)

    print("P5_B3_SKAG_CONTRACT=EXACT_PASS")
    print("P5_B3_SKAG_PROFILES=4_OF_4_EXACT_PASS")
    print("P5_B3_SKAG_VECTORS=1056_OF_1056_EXACT_PASS")
    print("P5_B3_SKAG_INFEASIBLE_AND_SATURATION=EXACT_PASS")
    print("P5_B3_BOARD_CASES=16_OF_16_EXACT_PASS")
    print("P5_B3_STAGE_A=PASS")


if __name__ == "__main__":
    main()
