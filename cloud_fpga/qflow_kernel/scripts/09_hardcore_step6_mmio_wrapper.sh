#!/usr/bin/env bash
set -euo pipefail

echo "[QFlow local hardening step 6] AWS-style MMIO/register-map wrapper readiness"
echo "Repo subdir: $(pwd)"

mkdir -p results/mmio_wrapper
rm -f results/mmio_wrapper/* || true

if [ -f sw/generate_randomized_golden_vectors.py ]; then
  echo "[0/6] Regenerate fixed-seed 215-vector package"
  python3 sw/generate_randomized_golden_vectors.py > results/mmio_wrapper/vector_generation.log 2>&1
else
  echo "Missing sw/generate_randomized_golden_vectors.py. Run Step 2 patch first."
  exit 1
fi
cat results/mmio_wrapper/vector_generation.log

echo "[1/6] Generate MMIO wrapper testbench"
python3 sw/generate_mmio_tb_from_vectors.py > results/mmio_wrapper/mmio_tb_generation.log 2>&1
cat results/mmio_wrapper/mmio_tb_generation.log

echo "[2/6] Compile MMIO wrapper testbench with Icarus -Wall"
iverilog -g2012 -Wall \
  -o results/mmio_wrapper/mmio_tb.out \
  tb/tb_qflow_mmio_regs.v \
  rtl/qflow_mmio_regs.v \
  rtl/fdpe_kernel.v \
  rtl/skag_weight_kernel.v \
  rtl/path_selector_kernel.v \
  rtl/qflow_cloud_kernel.v \
  > results/mmio_wrapper/iverilog_mmio_wall.log 2>&1

echo "Icarus MMIO compile/elaboration PASS"
if [ -s results/mmio_wrapper/iverilog_mmio_wall.log ]; then
  echo "Icarus MMIO -Wall log is not empty. Showing it:"
  cat results/mmio_wrapper/iverilog_mmio_wall.log
else
  echo "Icarus MMIO -Wall log is empty: no warnings/errors emitted."
fi

echo "[3/6] Run MMIO/register-map simulation"
vvp results/mmio_wrapper/mmio_tb.out | tee results/mmio_wrapper/mmio_sim.log

grep -i "MMIO WRAPPER PASS" results/mmio_wrapper/mmio_sim.log
cp results/mmio_output.csv results/mmio_wrapper/mmio_output.csv

echo "[4/6] Compare MMIO output against golden vectors"
python3 sw/compare_hw_vs_golden.py \
  --golden vectors/golden_vectors.csv \
  --hw results/mmio_wrapper/mmio_output.csv \
  --out results/mmio_wrapper/mmio_vs_python.csv

python3 - <<'PY'
import pandas as pd
from pathlib import Path

cmp_path = Path("results/mmio_wrapper/mmio_vs_python.csv")
df = pd.read_csv(cmp_path)
pass_count = int((df["pass_fail"].astype(str).str.upper() == "PASS").sum())
fail_count = int((df["pass_fail"].astype(str).str.upper() != "PASS").sum())
print(f"MMIO compare rows: {len(df)}")
print(f"MMIO compare PASS={pass_count}, FAIL={fail_count}")
if len(df) != 215:
    raise SystemExit(f"Expected 215 MMIO compare rows, got {len(df)}")
if pass_count != 215 or fail_count != 0:
    raise SystemExit("MMIO comparison failed")
PY

echo "[5/6] Optional Verilator lint for MMIO wrapper top"
if command -v verilator >/dev/null 2>&1; then
  set +e
  verilator --lint-only -Wall -Wno-fatal \
    --top-module qflow_mmio_regs \
    rtl/qflow_mmio_regs.v \
    rtl/fdpe_kernel.v \
    rtl/skag_weight_kernel.v \
    rtl/path_selector_kernel.v \
    rtl/qflow_cloud_kernel.v \
    > results/mmio_wrapper/verilator_mmio_lint.log 2>&1
  VERILATOR_RC=$?
  set -e
  cat results/mmio_wrapper/verilator_mmio_lint.log || true
  if [ "$VERILATOR_RC" -ne 0 ]; then
    echo "VERILATOR_MMIO_LINT=FAIL rc=$VERILATOR_RC" | tee results/mmio_wrapper/verilator_mmio_status.txt
    exit 1
  else
    echo "VERILATOR_MMIO_LINT=PASS" | tee results/mmio_wrapper/verilator_mmio_status.txt
  fi
else
  echo "VERILATOR_MMIO_LINT=SKIP_NOT_INSTALLED" | tee results/mmio_wrapper/verilator_mmio_status.txt
fi

echo "[6/6] Optional Yosys generic synthesis for MMIO wrapper top"
if command -v yosys >/dev/null 2>&1; then
  cat > results/mmio_wrapper/yosys_mmio_synth.ys <<'YS'
read_verilog -sv rtl/fdpe_kernel.v
read_verilog -sv rtl/skag_weight_kernel.v
read_verilog -sv rtl/path_selector_kernel.v
read_verilog -sv rtl/qflow_cloud_kernel.v
read_verilog -sv rtl/qflow_mmio_regs.v
hierarchy -check -top qflow_mmio_regs
proc
opt
memory
opt
techmap
opt
stat
write_json results/mmio_wrapper/qflow_mmio_regs_yosys.json
YS

  set +e
  yosys -s results/mmio_wrapper/yosys_mmio_synth.ys > results/mmio_wrapper/yosys_mmio_synth.log 2>&1
  YOSYS_RC=$?
  set -e
  tail -80 results/mmio_wrapper/yosys_mmio_synth.log || true
  if [ "$YOSYS_RC" -ne 0 ]; then
    echo "YOSYS_MMIO_SYNTH=FAIL rc=$YOSYS_RC" | tee results/mmio_wrapper/yosys_mmio_status.txt
    exit 1
  else
    echo "YOSYS_MMIO_SYNTH=PASS" | tee results/mmio_wrapper/yosys_mmio_status.txt
  fi
else
  echo "YOSYS_MMIO_SYNTH=SKIP_NOT_INSTALLED" | tee results/mmio_wrapper/yosys_mmio_status.txt
fi

SNAP=results/evidence_snapshot_07_mmio_wrapper_pass
rm -rf "$SNAP"
mkdir -p "$SNAP"
cp vectors/golden_vectors.csv "$SNAP/"
cp vectors/exp_lut.hex "$SNAP/"
cp results/mmio_wrapper/mmio_output.csv "$SNAP/"
cp results/mmio_wrapper/mmio_vs_python.csv "$SNAP/"
cp results/mmio_wrapper/mmio_sim.log "$SNAP/"
cp results/mmio_wrapper/iverilog_mmio_wall.log "$SNAP/"
cp results/mmio_wrapper/verilator_mmio_status.txt "$SNAP/"
cp results/mmio_wrapper/yosys_mmio_status.txt "$SNAP/"
[ -f results/mmio_wrapper/verilator_mmio_lint.log ] && cp results/mmio_wrapper/verilator_mmio_lint.log "$SNAP/"
[ -f results/mmio_wrapper/yosys_mmio_synth.log ] && cp results/mmio_wrapper/yosys_mmio_synth.log "$SNAP/"

cat > "$SNAP/README.md" <<'MD'
# QFlow Cloud FPGA Kernel — Evidence Snapshot 07

This snapshot records Hardcore Local Check Step 6 before AWS EC2 F2 launch.

## Result

- AWS-style local MMIO/register wrapper simulation: PASS
- Golden vectors used: 215
- MMIO transactions compared against Python golden vectors: 215
- Icarus Verilog `-Wall` compile/elaboration: PASS
- MMIO hardware-output CSV vs Python golden CSV: PASS
- Verilator MMIO lint: see `verilator_mmio_status.txt`
- Yosys MMIO generic synthesis: see `yosys_mmio_status.txt`

## Claim boundary

This is still local register-wrapper simulation/static-check evidence only. It is not AWS F2 physical FPGA execution evidence yet.

The wrapper is a local stand-in for the future AWS CL/OCL/MMIO attachment. It proves that the QFlow cloud kernel can be controlled through a host-style register map before paid F2 time is used.
MD

echo "MMIO WRAPPER AUDIT PASS"
echo "Snapshot written: $SNAP"
echo "STEP 6 PASS: AWS-style MMIO/register-map wrapper is locally clean."
