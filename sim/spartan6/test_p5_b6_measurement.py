#!/usr/bin/env python3
from collections import defaultdict
import csv
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
iv = shutil.which("iverilog")
vv = shutil.which("vvp")
if not iv or not vv:
    raise SystemExit("ERROR: install iverilog and vvp")

sources = [
    root / "rtl/rl/rl_state_encoder.v",
    root / "rtl/rl/rl_policy_rom.v",
    root / "rtl/rl/rl_profile_rom.v",
    root / "rtl/rl/rl_controller.v",
    root / "rtl/spartan6/p5_b4_candidate_evaluator.v",
    root / "rtl/spartan6/p5_b5_policy_shell.v",
    root / "rtl/spartan6/p5_b6_measurement_shell.v",
    root / "sim/spartan6/tb_p5_b6_measurement_shell.v",
]
for path in sources:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"ERROR: missing {path}")

wrapper = (root / "rtl/spartan6/p5_b6_measurement_shell.v").read_text()
for phrase in (
    "wire accepted = start && ready;",
    "assign cycles_valid = done;",
    "measurement_active",
    "kernel_cycle_counter",
    "UART serialization",
    ".cycles(ignored_b5_cycles)",
):
    if phrase not in wrapper:
        raise SystemExit(f"ERROR: B6 contract phrase missing: {phrase}")

def execute():
    with tempfile.TemporaryDirectory(prefix="qflow-p5-b6-") as td:
        exe = Path(td) / "p5_b6_tb.vvp"
        compile_result = subprocess.run(
            [iv, "-g2005", "-Wall", "-Wimplicit",
             "-s", "tb_p5_b6_measurement_shell",
             "-o", str(exe), *map(str, sources)],
            cwd=root, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, check=False,
        )
        if compile_result.returncode:
            print(compile_result.stdout, end="")
            raise SystemExit("P5_B6_IVERILOG_COMPILE=FAIL")

        run_result = subprocess.run(
            [vv, str(exe)], cwd=root, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
        )
        if run_result.returncode:
            print(run_result.stdout, end="")
            raise SystemExit("P5_B6_RTL_RUN=FAIL")
        return compile_result.stdout, run_result.stdout

compile_a, run_a = execute()
compile_b, run_b = execute()

print(compile_a, end="")
print("P5_B6_IVERILOG_COMPILE=PASS")
print(run_a, end="")

if run_a != run_b:
    raise SystemExit("P5_B6_REPRODUCIBILITY=FAIL")
if "P5_B6_MEASUREMENT=100_OF_100_COMPLETIONS_PASS" not in run_a:
    raise SystemExit("P5_B6_COMPLETION_SENTINEL=FAIL")
if "P5_B6_MEASUREMENT=FAIL" in run_a:
    raise SystemExit("P5_B6_FAILURE_MARKER=FOUND")

pattern = re.compile(r"^MEASURE case=(\d+) mode=(H[0-4]) cycles=(\d+)$")
rows = []
for line in run_a.splitlines():
    match = pattern.match(line)
    if match:
        case_id, mode, cycles = match.groups()
        rows.append((int(case_id), mode, int(cycles)))

if len(rows) != 100:
    raise SystemExit(f"P5_B6_MEASUREMENT_ROW_COUNT=FAIL_{len(rows)}")

seen = {(case_id, mode) for case_id, mode, _ in rows}
if len(seen) != 100:
    raise SystemExit("P5_B6_MEASUREMENT_UNIQUENESS=FAIL")
if any(cycles <= 0 for _, _, cycles in rows):
    raise SystemExit("P5_B6_NONPOSITIVE_CYCLE=FAIL")

out_dir = root / "results/nexys3/p5_step8_b6"
out_dir.mkdir(parents=True, exist_ok=True)

csv_path = out_dir / "kernel_cycle_measurements.csv"
with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["case_id", "policy_mode", "kernel_cycles"])
    writer.writerows(rows)

by_mode = defaultdict(list)
for _, mode, cycles in rows:
    by_mode[mode].append(cycles)

summary_path = out_dir / "kernel_cycle_summary.csv"
with summary_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["policy_mode", "samples", "minimum_cycles", "maximum_cycles", "mean_cycles"])
    for mode in ("H0", "H1", "H2", "H3", "H4"):
        values = by_mode[mode]
        writer.writerow([
            mode, len(values), min(values), max(values),
            f"{sum(values) / len(values):.6f}",
        ])

print("P5_B6_REPRODUCIBILITY=BYTE_EXACT_PASS")
print("P5_B6_MEASUREMENT_ROWS=100")
print(f"P5_B6_MEASUREMENT_CSV={csv_path.relative_to(root)}")
print(f"P5_B6_SUMMARY_CSV={summary_path.relative_to(root)}")
print("P5_B6_MEASUREMENT_PROTOCOL=PASS")
