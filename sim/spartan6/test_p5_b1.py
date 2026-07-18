#!/usr/bin/env python3
"""Deterministic P5 B1 Stage-A source, UCF and RTL-simulation gate."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RTL = [
    ROOT / "rtl/spartan6/p5_b1_uart_tx.v",
    ROOT / "rtl/spartan6/p5_b1_sevenseg.v",
    ROOT / "rtl/spartan6/p5_b1_top.v",
]
TB = ROOT / "sim/spartan6/tb_p5_b1_io_sanity.v"
UCF = ROOT / "constraints/nexys3/p5_b1_io_sanity.ucf"
DOC = ROOT / "docs/rl/p5_b1_io_sanity.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    files = [*RTL, TB, UCF, DOC]
    require(all(path.is_file() for path in files), "B1 Stage-A source set incomplete")

    rtl_text = "\n".join(path.read_text(encoding="utf-8") for path in RTL)
    ucf_text = UCF.read_text(encoding="utf-8")
    doc_text = DOC.read_text(encoding="utf-8")

    forbidden = ("always_ff", "always_comb", "logic ", "typedef", "interface ")
    require(not any(token in rtl_text for token in forbidden), "non-Verilog-2001 token found")
    require("module p5_b1_top" in rtl_text, "top module missing")
    require("QF5B1" in doc_text and "115200" in doc_text, "frozen B1 UART contract missing")

    expected_pins = {
        "clk_100mhz": "V10",
        "btn_reset": "B8",
        "led_heartbeat": "U16",
        "led_reset": "V16",
        "seg_n<0>": "T17",
        "seg_n<1>": "T18",
        "seg_n<2>": "U17",
        "seg_n<3>": "U18",
        "seg_n<4>": "M14",
        "seg_n<5>": "N14",
        "seg_n<6>": "L14",
        "seg_n<7>": "M13",
        "an_n<0>": "N16",
        "an_n<1>": "N15",
        "an_n<2>": "P18",
        "an_n<3>": "P17",
        "uart_tx": "N18",
    }
    for signal, pin in expected_pins.items():
        pattern = rf'NET\s+"{re.escape(signal)}"\s+LOC\s*=\s*"{pin}"'
        require(re.search(pattern, ucf_text), f"missing UCF mapping {signal}={pin}")

    require('PERIOD "P5_B1_CLK" 10 ns HIGH 50%' in ucf_text, "10 ns constraint missing")
    require(ucf_text.count(' LOC = "') == len(expected_pins), "unexpected UCF LOC count")

    divider = (100_000_000 + (115_200 // 2)) // 115_200
    actual_baud = 100_000_000 / divider
    baud_error_percent = 100.0 * (actual_baud - 115_200) / 115_200
    require(divider == 868, "unexpected UART divider")
    require(abs(baud_error_percent) < 0.01, "UART baud error exceeds frozen limit")

    iverilog = shutil.which("iverilog")
    vvp = shutil.which("vvp")
    require(iverilog is not None and vvp is not None, "iverilog/vvp not available")

    with tempfile.TemporaryDirectory(prefix="qflow_p5_b1_") as temporary:
        executable = Path(temporary) / "p5_b1_sim.out"
        compile_run = subprocess.run(
            [
                iverilog,
                "-g2005",
                "-Wall",
                "-s",
                "tb_p5_b1_io_sanity",
                "-o",
                str(executable),
                *(str(path) for path in RTL),
                str(TB),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
            check=False,
        )
        require(compile_run.returncode == 0, "iverilog compile failed:\n" + compile_run.stdout)
        require("warning" not in compile_run.stdout.lower(), "iverilog warning:\n" + compile_run.stdout)

        simulation = subprocess.run(
            [vvp, str(executable)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
            check=False,
        )
        require(simulation.returncode == 0, "RTL simulation failed:\n" + simulation.stdout)
        required_markers = (
            "P5_B1_SIM_UART_BYTES=16_OF_16_PASS",
            "P5_B1_SIM_DISPLAY_DIGITS=4_OF_4_PASS",
            "P5_B1_SIM_RESET_CASES=2_OF_2_PASS",
            "P5_B1_SIM=PASS",
        )
        require(all(marker in simulation.stdout for marker in required_markers), simulation.stdout)

    print("P5_B1_STAGE_A_STATIC_CHECKS=7_PASS")
    print("P5_B1_UCF_LOCATIONS=17_OF_17_PASS")
    print("P5_B1_CLOCK_CONSTRAINT_10NS=PASS")
    print("P5_B1_UART_DIVIDER=868_PASS")
    print("P5_B1_UART_BAUD_ERROR_PERCENT=+0.0064004096_PASS")
    print("P5_B1_SIM_UART_BYTES=16_OF_16_PASS")
    print("P5_B1_SIM_DISPLAY_DIGITS=4_OF_4_PASS")
    print("P5_B1_SIM_RESET_CASES=2_OF_2_PASS")
    print("P5_B1_STAGE_A=PASS")


if __name__ == "__main__":
    main()
