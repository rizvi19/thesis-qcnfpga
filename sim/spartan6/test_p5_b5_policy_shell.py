#!/usr/bin/env python3
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
iv = shutil.which("iverilog")
vv = shutil.which("vvp")
if not iv or not vv:
    raise SystemExit("ERROR: install iverilog and vvp")

required = [
    root / "rtl/rl/rl_state_encoder.v",
    root / "rtl/rl/rl_policy_rom.v",
    root / "rtl/rl/rl_profile_rom.v",
    root / "rtl/rl/rl_controller.v",
    root / "rtl/spartan6/p5_b4_candidate_evaluator.v",
    root / "rtl/spartan6/p5_b5_policy_shell.v",
    root / "sim/spartan6/tb_p5_b5_policy_shell.v",
    root / "results/rl/p3_export/policy_rom.mem",
    root / "results/rl/p3_export/profile_rom.mem",
]
for path in required:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"ERROR: missing {path}")

text = (root / "rtl/spartan6/p5_b5_policy_shell.v").read_text()
for phrase in (
    "POLICY_MODE",
    "H0 = 3'd0",
    "H1 = 3'd1",
    "H2 = 3'd2",
    "H3 = 3'd3",
    "H4 = 3'd4",
    "key_bin == 2'd0",
    "fid_bin <= 2'd1",
    "imbalance_bin >= 2'd2",
    "cycles_valid = 1'b0",
):
    if phrase not in text:
        raise SystemExit(f"ERROR: contract phrase missing: {phrase}")

with tempfile.TemporaryDirectory(prefix="qflow-p5-b5-") as td:
    exe = Path(td) / "p5_b5_tb.vvp"
    cmd = [
        iv, "-g2005", "-Wall", "-Wimplicit",
        "-s", "tb_p5_b5_policy_shell",
        "-o", str(exe),
        str(root / "rtl/rl/rl_state_encoder.v"),
        str(root / "rtl/rl/rl_policy_rom.v"),
        str(root / "rtl/rl/rl_profile_rom.v"),
        str(root / "rtl/rl/rl_controller.v"),
        str(root / "rtl/spartan6/p5_b4_candidate_evaluator.v"),
        str(root / "rtl/spartan6/p5_b5_policy_shell.v"),
        str(root / "sim/spartan6/tb_p5_b5_policy_shell.v"),
    ]
    compile_result = subprocess.run(
        cmd, cwd=root, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=False
    )
    print(compile_result.stdout, end="")
    if compile_result.returncode:
        raise SystemExit("P5_B5_IVERILOG_COMPILE=FAIL")
    print("P5_B5_IVERILOG_COMPILE=PASS")

    run_result = subprocess.run(
        [vv, str(exe)], cwd=root, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
    )
    print(run_result.stdout, end="")
    if run_result.returncode:
        raise SystemExit("P5_B5_RTL_RUN=FAIL")
    if "P5_B5_HOST_TEST=101_OF_101_MODE_RESULTS_PASS" not in run_result.stdout:
        raise SystemExit("P5_B5_RTL_SENTINEL=FAIL")
    if "P5_B5_HOST_TEST=FAIL" in run_result.stdout:
        raise SystemExit("P5_B5_RTL_FAILURE_MARKER=FOUND")

print("P5_B5_POLICY_SHELL_VERIFICATION=PASS")
