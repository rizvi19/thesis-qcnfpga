#!/usr/bin/env bash
set -euo pipefail

echo "[QFlow local hardening step 5] Static lint / elaboration / generic synthesis checks"
echo "Repo subdir: $(pwd)"

mkdir -p results/lint_static
rm -f results/lint_static/* || true

echo "[0/5] Regenerate fixed-seed 215-vector regression package"
python3 sw/generate_randomized_golden_vectors.py > results/lint_static/vector_generation.log 2>&1
cat results/lint_static/vector_generation.log

python3 sw/generate_tb_from_vectors.py > results/lint_static/testbench_generation.log 2>&1
cat results/lint_static/testbench_generation.log

echo "[1/5] Icarus Verilog compile/elaboration with -Wall"
iverilog -g2012 -Wall \
  -o results/lint_static/iverilog_wall_tb.out \
  tb/tb_qflow_cloud_kernel.v \
  rtl/fdpe_kernel.v \
  rtl/skag_weight_kernel.v \
  rtl/path_selector_kernel.v \
  rtl/qflow_cloud_kernel.v \
  > results/lint_static/iverilog_wall.log 2>&1

echo "Icarus compile/elaboration PASS"

if [ -s results/lint_static/iverilog_wall.log ]; then
  echo "Icarus -Wall log is not empty. Showing it:"
  cat results/lint_static/iverilog_wall.log
else
  echo "Icarus -Wall log is empty: no warnings/errors emitted."
fi

echo "[2/5] Run simulation from strict-compiled output"
vvp results/lint_static/iverilog_wall_tb.out | tee results/lint_static/iverilog_wall_sim.log

grep -i "ALL TESTS PASS" results/lint_static/iverilog_wall_sim.log
cp results/hardware_output.csv results/lint_static/hardware_output_static.csv

echo "[3/5] Compare hardware-output CSV against golden CSV"
python3 sw/compare_hw_vs_golden.py \
  --golden vectors/golden_vectors.csv \
  --hw results/lint_static/hardware_output_static.csv \
  --out results/lint_static/hardware_vs_python_static.csv

python3 - <<'PY'
import pandas as pd
from pathlib import Path

cmp_path = Path("results/lint_static/hardware_vs_python_static.csv")
df = pd.read_csv(cmp_path)

if "pass_fail" in df.columns:
    pass_count = int((df["pass_fail"].astype(str).str.upper() == "PASS").sum())
    fail_count = int((df["pass_fail"].astype(str).str.upper() != "PASS").sum())
elif "status" in df.columns:
    pass_count = int((df["status"].astype(str).str.upper() == "PASS").sum())
    fail_count = int((df["status"].astype(str).str.upper() != "PASS").sum())
elif "match" in df.columns:
    pass_count = int(df["match"].astype(bool).sum())
    fail_count = int((~df["match"].astype(bool)).sum())
else:
    raise SystemExit(
        f"Could not find pass_fail/status/match column in {cmp_path}. Columns={list(df.columns)}"
    )

print(f"Static compare rows: {len(df)}")
print(f"Static compare PASS={pass_count}, FAIL={fail_count}")

if len(df) != 215:
    raise SystemExit(f"Expected 215 compare rows, got {len(df)}")
if pass_count != 215:
    raise SystemExit(f"Expected 215 PASS rows, got {pass_count}")
if fail_count != 0:
    raise SystemExit(f"Expected 0 failures, got {fail_count}")
PY

echo "[4/5] Optional Verilator lint"
if command -v verilator >/dev/null 2>&1; then
  set +e
  verilator --lint-only -Wall -Wno-fatal \
    --top-module qflow_cloud_kernel \
    rtl/fdpe_kernel.v \
    rtl/skag_weight_kernel.v \
    rtl/path_selector_kernel.v \
    rtl/qflow_cloud_kernel.v \
    > results/lint_static/verilator_lint.log 2>&1
  VERILATOR_RC=$?
  set -e

  cat results/lint_static/verilator_lint.log || true

  if [ "$VERILATOR_RC" -ne 0 ]; then
    echo "VERILATOR_LINT=FAIL rc=$VERILATOR_RC" | tee results/lint_static/verilator_status.txt
    exit 1
  else
    echo "VERILATOR_LINT=PASS" | tee results/lint_static/verilator_status.txt
  fi
else
  echo "VERILATOR_LINT=SKIP_NOT_INSTALLED" | tee results/lint_static/verilator_status.txt
fi

echo "[5/5] Optional Yosys generic synthesis"
if command -v yosys >/dev/null 2>&1; then
  cat > results/lint_static/yosys_synth.ys <<'YS'
read_verilog -sv rtl/fdpe_kernel.v
read_verilog -sv rtl/skag_weight_kernel.v
read_verilog -sv rtl/path_selector_kernel.v
read_verilog -sv rtl/qflow_cloud_kernel.v
hierarchy -check -top qflow_cloud_kernel
proc
opt
memory
opt
techmap
opt
stat
write_json results/lint_static/qflow_cloud_kernel_yosys.json
YS

  set +e
  yosys -s results/lint_static/yosys_synth.ys > results/lint_static/yosys_synth.log 2>&1
  YOSYS_RC=$?
  set -e

  tail -80 results/lint_static/yosys_synth.log || true

  if [ "$YOSYS_RC" -ne 0 ]; then
    echo "YOSYS_GENERIC_SYNTH=FAIL rc=$YOSYS_RC" | tee results/lint_static/yosys_status.txt
    exit 1
  else
    echo "YOSYS_GENERIC_SYNTH=PASS" | tee results/lint_static/yosys_status.txt
  fi
else
  echo "YOSYS_GENERIC_SYNTH=SKIP_NOT_INSTALLED" | tee results/lint_static/yosys_status.txt
fi

echo "[Snapshot] Save evidence snapshot 06"
SNAP=results/evidence_snapshot_06_static_lint_pass
rm -rf "$SNAP"
mkdir -p "$SNAP"

cp vectors/golden_vectors.csv "$SNAP/"
cp vectors/exp_lut.hex "$SNAP/"
cp results/lint_static/iverilog_wall.log "$SNAP/"
cp results/lint_static/iverilog_wall_sim.log "$SNAP/"
cp results/lint_static/hardware_output_static.csv "$SNAP/"
cp results/lint_static/hardware_vs_python_static.csv "$SNAP/"
cp results/lint_static/verilator_status.txt "$SNAP/"
cp results/lint_static/yosys_status.txt "$SNAP/"

if [ -f results/lint_static/verilator_lint.log ]; then
  cp results/lint_static/verilator_lint.log "$SNAP/"
fi

if [ -f results/lint_static/yosys_synth.log ]; then
  cp results/lint_static/yosys_synth.log "$SNAP/"
fi

cat > "$SNAP/README.md" <<'MD'
# QFlow Cloud FPGA Kernel — Evidence Snapshot 06

This snapshot records Hardcore Local Check Step 5 before AWS EC2 F2 launch.

## Result

- Golden vectors regenerated: 215
- Icarus Verilog compile/elaboration with `-Wall`: PASS
- RTL simulation from strict-compiled output: PASS
- Hardware-output CSV vs Python golden CSV: PASS
- Verilator lint: see `verilator_status.txt`
- Yosys generic synthesis: see `yosys_status.txt`

## Claim boundary

This is still local RTL/static-check evidence only. It is not AWS F2 physical FPGA execution evidence yet.

Yosys generic synthesis, if available, is only a local sanity check. It is not a replacement for AWS HDK/Vivado AFI build.
MD

echo "STATIC LINT AUDIT PASS"
echo "Snapshot written: $SNAP"
echo "STEP 5 PASS: static lint/elaboration/generic-synthesis local gate is clean."
