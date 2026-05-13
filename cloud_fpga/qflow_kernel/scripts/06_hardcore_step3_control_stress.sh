#!/usr/bin/env bash
set -euo pipefail

echo "[QFlow local hardening step 3] Control/reset/start-pulse stress"
echo "Repo subdir: $(pwd)"

SNAPSHOT_DIR="results/evidence_snapshot_04_control_stress_pass"

if [ ! -f vectors/golden_vectors.csv ]; then
  echo "ERROR: vectors/golden_vectors.csv not found. Run Step 2 first."
  exit 1
fi

mkdir -p results
rm -f results/qflow_control_stress_tb.out \
      results/control_stress_output.csv \
      results/control_stress_log.txt

python3 sw/generate_control_stress_tb.py

iverilog -g2012 -o results/qflow_control_stress_tb.out \
  tb/tb_qflow_control_stress.v \
  rtl/fdpe_kernel.v \
  rtl/skag_weight_kernel.v \
  rtl/path_selector_kernel.v \
  rtl/qflow_cloud_kernel.v

vvp results/qflow_control_stress_tb.out | tee results/control_stress_log.txt

grep -i "CONTROL STRESS PASS" results/control_stress_log.txt

python3 - <<'PY'
from pathlib import Path
import csv

root = Path('.')
log_path = root / 'results/control_stress_log.txt'
csv_path = root / 'results/control_stress_output.csv'
golden_path = root / 'vectors/golden_vectors.csv'

log = log_path.read_text(errors='ignore')
errors = []

if 'CONTROL STRESS PASS' not in log:
    errors.append('Missing CONTROL STRESS PASS in log')
if 'FAIL_CONTROL' in log:
    errors.append('Control stress log contains FAIL_CONTROL')
if 'CONTROL STRESS FAILED' in log:
    errors.append('Control stress log contains CONTROL STRESS FAILED')

with golden_path.open() as f:
    golden_rows = list(csv.DictReader(f))
expected_golden = len(golden_rows)
expected_btb = min(32, expected_golden)
expected_csv_rows = expected_golden + expected_btb

with csv_path.open() as f:
    stress_rows = list(csv.DictReader(f))

if len(stress_rows) != expected_csv_rows:
    errors.append(f'Expected {expected_csv_rows} control CSV rows, got {len(stress_rows)}')

latencies = sorted({int(r['latency_cycles']) for r in stress_rows}) if stress_rows else []
if latencies != [2]:
    errors.append(f'Expected latency_cycles [2] in pulse/back-to-back rows, got {latencies}')

modes = {}
for r in stress_rows:
    modes[r['mode']] = modes.get(r['mode'], 0) + 1
if modes.get('pulse', 0) != expected_csv_rows:
    errors.append(f'Expected {expected_csv_rows} recorded transaction rows, got {modes.get("pulse", 0)}')
# Back-to-back rows reuse run_pulse_and_check internally but their test_id prefix is BTB_.
btb_count = sum(1 for r in stress_rows if r['test_id'].startswith('BTB_'))
if btb_count != expected_btb:
    errors.append(f'Expected {expected_btb} BTB rows, got {btb_count}')

for r in stress_rows:
    flags = int(r['status_flags'])
    done = flags & 1
    valid = (flags >> 1) & 1
    no_path = (flags >> 2) & 1
    exp_valid = int(r['expected_valid_path'])
    if done != 1:
        errors.append(f"{r['test_id']}: done bit was not high in recorded transaction")
        break
    if exp_valid == 1 and valid != 1:
        errors.append(f"{r['test_id']}: expected valid path but valid bit not set")
        break
    if exp_valid == 0 and no_path != 1:
        errors.append(f"{r['test_id']}: expected no path but no_path bit not set")
        break

if errors:
    print('Control stress audit FAILED')
    for e in errors:
        print(' -', e)
    raise SystemExit(1)

snap = root / 'results/evidence_snapshot_04_control_stress_pass'
snap.mkdir(parents=True, exist_ok=True)
for src_name in [
    'results/control_stress_log.txt',
    'results/control_stress_output.csv',
    'vectors/golden_vectors.csv',
    'vectors/exp_lut.hex',
]:
    src = root / src_name
    dst = snap / Path(src_name).name
    dst.write_bytes(src.read_bytes())

readme = f"""# QFlow Cloud FPGA Kernel — Evidence Snapshot 04

This snapshot records Hardcore Local Check Step 3 before AWS EC2 F2 launch.

## Result

- Golden vectors reused: {expected_golden}
- Full pulse-control transaction checks: {expected_golden}
- Back-to-back transaction subset checks: {expected_btb}
- Reset-output check: PASS
- Start-during-reset ignored check: PASS
- Reset-mid-transaction clear check: PASS
- RTL compile: PASS
- RTL simulation: PASS
- Control stress rows recorded: {len(stress_rows)}
- Latency cycles observed in transaction rows: {latencies}

## Coverage purpose

This step checks the control behavior around the already-passing QFlow cloud kernel: synchronous reset, start pulse, done pulse width, status flags, latency counter reset, repeated transactions, and reset during an active transaction.

## Claim boundary

This is still local RTL simulation evidence only. It is not AWS F2 physical FPGA execution evidence yet.
"""
(snap / 'README.md').write_text(readme)

print('Control stress audit PASS')
print(f'Golden vectors reused: {expected_golden}')
print(f'Recorded transaction rows: {modes.get("pulse", 0)}')
print(f'BTB rows: {btb_count}')
print(f'Control CSV rows: {len(stress_rows)}')
print(f'Latency cycles observed: {latencies}')
print(f'Snapshot written: {snap}')
PY

echo "STEP 3 PASS: control/reset/start-pulse local stress is clean."
