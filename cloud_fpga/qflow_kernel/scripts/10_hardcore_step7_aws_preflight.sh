#!/usr/bin/env bash
set -euo pipefail

echo "[QFlow local hardening step 7] AWS preflight evidence manifest and launch-readiness audit"
echo "Repo subdir: $(pwd)"

mkdir -p results/aws_preflight
rm -f results/aws_preflight/* || true

required_files=(
  "rtl/fdpe_kernel.v"
  "rtl/skag_weight_kernel.v"
  "rtl/path_selector_kernel.v"
  "rtl/qflow_cloud_kernel.v"
  "rtl/qflow_mmio_regs.v"
  "sw/generate_golden_vectors.py"
  "sw/generate_randomized_golden_vectors.py"
  "sw/generate_tb_from_vectors.py"
  "sw/generate_mmio_tb_from_vectors.py"
  "sw/compare_hw_vs_golden.py"
  "vectors/golden_vectors.csv"
  "vectors/exp_lut.hex"
  "docs/aws_mmio_register_map.md"
)

required_snapshots=(
  "results/evidence_snapshot_02_extended_local_pass"
  "results/evidence_snapshot_03_fixed_seed_random_pass"
  "results/evidence_snapshot_04_control_stress_pass"
  "results/evidence_snapshot_05_x_sanity_pass"
  "results/evidence_snapshot_06_static_lint_pass"
  "results/evidence_snapshot_07_mmio_wrapper_pass"
)

echo "[1/6] Check required source/generated files"
missing=0
for f in "${required_files[@]}"; do
  if [ -f "$f" ]; then
    echo "FILE_OK $f"
  else
    echo "FILE_MISSING $f"
    missing=1
  fi
done
if [ "$missing" -ne 0 ]; then
  echo "STEP 7 FAIL: required files missing"
  exit 1
fi

echo "[2/6] Check evidence snapshot directories"
missing_snap=0
for d in "${required_snapshots[@]}"; do
  if [ -d "$d" ]; then
    echo "SNAPSHOT_OK $d"
  else
    echo "SNAPSHOT_MISSING $d"
    missing_snap=1
  fi
done
if [ "$missing_snap" -ne 0 ]; then
  echo "STEP 7 FAIL: required evidence snapshot missing"
  exit 1
fi

echo "[3/6] Generate evidence manifest"
python3 sw/collect_aws_preflight_manifest.py

echo "[4/6] Generate AWS host-driver skeletons"
python3 sw/generate_aws_host_driver_stub.py

echo "[5/6] Create local readiness note"
cat > results/aws_preflight/AWS_LOCAL_READY.md <<'MD'
# QFlow AWS F2 Local Readiness Note

## Status

The QFlow cloud-FPGA kernel has passed local pre-AWS hardening gates through the AWS-style MMIO/register-map wrapper stage.

## Local gates completed

- Gate 1: extended deterministic regression
- Gate 2: fixed-seed randomized regression
- Gate 3: reset/control/start-pulse stress
- Gate 4: X/Z output-sanity regression
- Gate 5: strict compile, lint-style checks, and generic synthesis
- Gate 6: AWS-style MMIO/register-map wrapper simulation and generic synthesis

## Evidence boundary

This package proves local RTL, control, MMIO, and generic synthesis readiness. It is not yet AWS F2 physical FPGA execution evidence.

## Next AWS action after this gate

Only after committing this gate should the AWS account/quota/budget/session setup begin. The first cloud session should run the official AWS FPGA example before integrating QFlow.
MD

echo "[6/6] Final checklist"
cat > results/aws_preflight/aws_preflight_checklist.txt <<'TXT'
AWS_PRELAUNCH_CHECKLIST
[ ] Branch pushed to GitHub: cloud-fpga-f2-kernel or equivalent
[ ] Git status clean before EC2 launch
[ ] AWS budgets created: $25, $50, $100 alerts
[ ] Root MFA enabled
[ ] No root access keys created
[ ] EC2 F-instance quota checked/requested
[ ] Region selected intentionally, preferably us-east-1 if available
[ ] Security group SSH source restricted to My IP only
[ ] f2.6xlarge selected intentionally, not f2.12xlarge/f2.48xlarge
[ ] Instance stop/terminate rule understood
[ ] Session cost log prepared
[ ] Official AWS FPGA example will be run before QFlow
TXT

cp docs/aws_preflight_checklist.md results/aws_preflight/ 2>/dev/null || true
cp docs/aws_session_zero_runbook.md results/aws_preflight/ 2>/dev/null || true
cp docs/aws_mmio_register_map.md results/aws_preflight/ 2>/dev/null || true

SNAP=results/evidence_snapshot_08_aws_preflight_ready
rm -rf "$SNAP"
mkdir -p "$SNAP"
cp -r results/aws_preflight/* "$SNAP/"

cat > "$SNAP/README.md" <<'MD'
# QFlow Cloud FPGA Kernel — Evidence Snapshot 08

This snapshot records Hardcore Local Check Step 7: AWS preflight evidence manifest and launch-readiness audit.

## Result

- Required RTL/source/vector/documentation files: present
- Required local evidence snapshots: present
- Evidence manifest generated
- AWS host-driver skeleton generated
- AWS local readiness note generated
- AWS prelaunch checklist generated

## Claim boundary

This is still local preflight evidence. It does not prove that an AWS EC2 F2 AFI has been built, loaded, or executed yet.
MD

echo "AWS PREFLIGHT AUDIT PASS"
echo "Snapshot written: $SNAP"
echo "STEP 7 PASS: AWS preflight evidence manifest and local launch-readiness audit is clean."
