#!/usr/bin/env bash
set -euo pipefail

echo "[QFlow local hardening step 2] Fixed-seed randomized regression"
echo "Repo subdir: $(pwd)"

EXPECTED_TOTAL=215
EXPECTED_RANDOM=200
SNAPSHOT_DIR="results/evidence_snapshot_03_fixed_seed_random_pass"

rm -f results/qflow_kernel_tb.out results/local_sim_output.txt results/hardware_output.csv results/hardware_vs_python.csv
mkdir -p results

python3 sw/generate_randomized_golden_vectors.py
python3 sw/generate_tb_from_vectors.py

iverilog -g2012 -o results/qflow_kernel_tb.out \
  tb/tb_qflow_cloud_kernel.v \
  rtl/fdpe_kernel.v \
  rtl/skag_weight_kernel.v \
  rtl/path_selector_kernel.v \
  rtl/qflow_cloud_kernel.v

vvp results/qflow_kernel_tb.out | tee results/local_sim_output.txt

grep -i "ALL TESTS PASS" results/local_sim_output.txt
python3 sw/compare_hw_vs_golden.py \
  --golden vectors/golden_vectors.csv \
  --hw results/hardware_output.csv \
  --out results/hardware_vs_python.csv

python3 - <<'PY'
from pathlib import Path
import pandas as pd

expected_total = 215
expected_random = 200
root = Path('.')
golden = pd.read_csv(root / 'vectors/golden_vectors.csv')
hw = pd.read_csv(root / 'results/hardware_output.csv')
cmp = pd.read_csv(root / 'results/hardware_vs_python.csv')
log = (root / 'results/local_sim_output.txt').read_text(errors='ignore')

errors = []
if len(golden) != expected_total:
    errors.append(f"Expected {expected_total} golden rows, got {len(golden)}")
if len(hw) != expected_total:
    errors.append(f"Expected {expected_total} hardware rows, got {len(hw)}")
if len(cmp) != expected_total:
    errors.append(f"Expected {expected_total} compare rows, got {len(cmp)}")
if (cmp['pass_fail'] != 'PASS').any():
    errors.append("At least one compare row is not PASS")
if 'ALL TESTS PASS' not in log:
    errors.append("Simulation log does not contain ALL TESTS PASS")
if 'FAIL' in log.upper():
    # The compare summary uses FAIL=0 sometimes; allow that exact phrase if present outside sim log.
    errors.append("Simulation log contains FAIL")
random_count = sum(str(x).startswith('R') for x in golden['test_id'])
if random_count != expected_random:
    errors.append(f"Expected {expected_random} randomized rows, got {random_count}")

latencies = sorted(set(int(x) for x in hw['latency_cycles']))
if latencies != [2]:
    errors.append(f"Expected stable latency_cycles [2], got {latencies}")

# Make sure randomized suite truly exercises both valid-path and no-path behavior.
valid_counts = golden['expected_valid_path'].value_counts().to_dict()
if valid_counts.get(1, 0) == 0:
    errors.append("No valid-path vectors found")
if valid_counts.get(0, 0) == 0:
    errors.append("No no-path vectors found")

# Hardware status sanity: valid rows should have bit1 set; no-path rows should have bit2 set.
merged = golden[['test_id', 'expected_valid_path']].merge(hw[['test_id', 'status_flags']], on='test_id', how='inner')
for _, row in merged.iterrows():
    flags = int(row['status_flags'])
    expected_valid = int(row['expected_valid_path'])
    done = flags & 0x1
    valid_bit = (flags >> 1) & 0x1
    no_path_bit = (flags >> 2) & 0x1
    if done != 1:
        errors.append(f"{row['test_id']}: done bit not set in status_flags={flags}")
        break
    if expected_valid == 1 and valid_bit != 1:
        errors.append(f"{row['test_id']}: valid expected but valid bit not set, status_flags={flags}")
        break
    if expected_valid == 0 and no_path_bit != 1:
        errors.append(f"{row['test_id']}: no_path expected but no_path bit not set, status_flags={flags}")
        break

if errors:
    print("Fixed-seed randomized regression audit FAILED")
    for e in errors:
        print(" -", e)
    raise SystemExit(1)

snap = root / 'results/evidence_snapshot_03_fixed_seed_random_pass'
snap.mkdir(parents=True, exist_ok=True)
for src_name in [
    'results/local_sim_output.txt',
    'results/hardware_output.csv',
    'results/hardware_vs_python.csv',
    'vectors/golden_vectors.csv',
    'vectors/exp_lut.hex',
]:
    src = root / src_name
    dst = snap / Path(src_name).name
    dst.write_bytes(src.read_bytes())

readme = f"""# QFlow Cloud FPGA Kernel — Evidence Snapshot 03

This snapshot records Hardcore Local Check Step 2 before AWS EC2 F2 launch.

## Result

- Deterministic vectors: 15
- Fixed-seed randomized vectors: {expected_random}
- Total vectors: {expected_total}
- RTL compile: PASS
- RTL simulation: PASS
- Hardware-output CSV vs Python golden CSV: PASS
- PASS rows: {len(cmp)}
- FAIL rows: 0
- Latency cycles observed in local wrapper: {latencies}
- Expected-valid distribution: {valid_counts}

## Coverage purpose

This step stress-tests the small QFlow cloud kernel under fixed-seed randomized combinations of edge validity, key scarcity, fidelity threshold, decay index, QBER, arrival-rate bucket, distance/cost, invalid edge IDs, zero-length candidates, valid-path outputs, and no-path outputs.

## Claim boundary

This is still local RTL simulation evidence only. It is not AWS F2 physical FPGA execution evidence yet.
"""
(snap / 'README.md').write_text(readme)
print("Fixed-seed randomized regression audit PASS")
print(f"Golden vectors: {len(golden)}")
print(f"Randomized vectors: {random_count}")
print(f"Hardware rows: {len(hw)}")
print(f"Compare rows: {len(cmp)}")
print(f"Latency cycles observed: {latencies}")
print(f"Expected-valid distribution: {valid_counts}")
print(f"Snapshot written: {snap}")
PY

echo "STEP 2 PASS: fixed-seed randomized local regression is clean."
