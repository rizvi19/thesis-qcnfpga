#!/usr/bin/env python3
"""Deterministic P5 B2 generator, contract and RTL simulation gate."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(command: list[str], timeout: int = 60) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    require(completed.returncode == 0, "command failed:\n" + completed.stdout)
    return completed.stdout


def main() -> None:
    contract = json.loads((ROOT / "rl/config/p5_qflow_mini_contract_v1.json").read_text())
    fdpe_contract = contract["fdpe_mini"]
    require(fdpe_contract["x_format"] == "UQ4.12", "FDPE x format drift")
    require(fdpe_contract["lut_depth"] == 256, "FDPE LUT depth drift")
    require(fdpe_contract["interpolation_fraction_denominator"] == 128, "FDPE fraction drift")
    require(fdpe_contract["final_multiply_rescale"] == "full_product_shift_right_16_truncate", "FDPE multiply drift")

    required = [
        ROOT / "tools/generate_p5_b2_fdpe_vectors.py",
        ROOT / "rtl/spartan6/p5_b2_fdpe.v",
        ROOT / "rtl/spartan6/p5_b2_selftest_top.v",
        ROOT / "rtl/spartan6/p5_b2_exp_lut.mem",
        ROOT / "rtl/spartan6/p5_b2_board_vectors.vh",
        ROOT / "sim/spartan6/p5_b2_fdpe_vectors.csv",
        ROOT / "sim/spartan6/p5_b2_fdpe_vectors.mem",
        ROOT / "sim/spartan6/tb_p5_b2_fdpe.v",
        ROOT / "sim/spartan6/tb_p5_b2_selftest.v",
    ]
    require(all(path.is_file() for path in required), "P5 B2 source set incomplete")
    text = "\n".join(path.read_text(encoding="utf-8") for path in required if path.suffix in {".v", ".vh"})
    require(not any(token in text for token in ("always_ff", "always_comb", "logic ", "typedef", "interface ")), "non-Verilog-2001 token")

    with tempfile.TemporaryDirectory(prefix="qflow_p5_b2_") as temp_name:
        temp = Path(temp_name)
        generated = {
            "lut": temp / "lut.mem",
            "csv": temp / "vectors.csv",
            "mem": temp / "vectors.mem",
            "board": temp / "board.vh",
        }
        generator_output = run(
            [
                shutil.which("python3") or "python3",
                str(required[0]),
                "--lut", str(generated["lut"]),
                "--csv", str(generated["csv"]),
                "--mem", str(generated["mem"]),
                "--board-vh", str(generated["board"]),
            ]
        )
        require("P5_B2_FDPE_VECTOR_COUNT=519" in generator_output, generator_output)
        comparisons = [
            (generated["lut"], required[3]),
            (generated["board"], required[4]),
            (generated["csv"], required[5]),
            (generated["mem"], required[6]),
        ]
        for actual, expected in comparisons:
            require(actual.read_bytes() == expected.read_bytes(), f"generator drift: {expected}")

        rows = list(csv.DictReader(required[5].open(encoding="utf-8")))
        require(len(rows) == 519, "unexpected vector count")
        require(sum(row["category"] == "lut_boundary" for row in rows) == 256, "boundary coverage differs")
        require(sum(row["category"] == "interpolation_midpoint" for row in rows) == 256, "interpolation coverage differs")

        iverilog = shutil.which("iverilog")
        vvp = shutil.which("vvp")
        require(iverilog is not None and vvp is not None, "iverilog/vvp unavailable")
        core_exe = temp / "core.out"
        compile_core = run([
            iverilog, "-g2005", "-Wall", "-s", "tb_p5_b2_fdpe", "-o", str(core_exe),
            "rtl/spartan6/p5_b2_fdpe.v", "sim/spartan6/tb_p5_b2_fdpe.v",
        ])
        require("warning" not in compile_core.lower(), compile_core)
        core_output = run([vvp, str(core_exe), "+VECTORS=sim/spartan6/p5_b2_fdpe_vectors.mem", "+COUNT=519"])
        require("P5_B2_FDPE_VECTORS=519_OF_519_EXACT_PASS" in core_output, core_output)

        board_exe = temp / "board.out"
        compile_board = run([
            iverilog, "-g2005", "-Wall", "-I", "rtl/spartan6", "-s", "tb_p5_b2_selftest", "-o", str(board_exe),
            "rtl/spartan6/p5_b2_fdpe.v", "rtl/spartan6/p5_b1_sevenseg.v",
            "rtl/spartan6/p5_b2_selftest_top.v", "sim/spartan6/tb_p5_b2_selftest.v",
        ])
        require("warning" not in compile_board.lower(), compile_board)
        board_output = run([vvp, str(board_exe)])
        require("P5_B2_BOARD_CASES=16_OF_16_EXACT_PASS" in board_output, board_output)

    print("P5_B2_FDPE_CONTRACT=EXACT_PASS")
    print("P5_B2_FDPE_LUT=256_OF_256_PASS")
    print("P5_B2_FDPE_BOUNDARIES=256_OF_256_PASS")
    print("P5_B2_FDPE_INTERPOLATIONS=256_OF_256_PASS")
    print("P5_B2_FDPE_VECTORS=519_OF_519_EXACT_PASS")
    print("P5_B2_FDPE_LATENCY=6_CYCLES_EXACT_PASS")
    print("P5_B2_BOARD_CASES=16_OF_16_EXACT_PASS")
    print("P5_B2_STAGE_A=PASS")


if __name__ == "__main__":
    main()
