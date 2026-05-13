#!/usr/bin/env bash
set -euo pipefail

echo "[QFlow local hardening step 4] X/Z output-sanity and clean-status regression"
echo "Repo subdir: $(pwd)"

EXPECTED_TOTAL=215
SNAPSHOT_DIR="results/evidence_snapshot_05_x_sanity_pass"

mkdir -p results
rm -f results/qflow_x_sanity_tb.out results/x_sanity_log.txt results/x_sanity_output.csv

# Recreate the fixed-seed dataset if the Step-2 generator is available. This keeps
# Step 4 reproducible from a clean checkout.
if [[ -f sw/generate_randomized_golden_vectors.py ]]; then
  python3 sw/generate_randomized_golden_vectors.py
else
  echo "ERROR: sw/generate_randomized_golden_vectors.py missing. Apply Step 2 patch first." >&2
  exit 1
fi

python3 sw/generate_x_sanity_tb.py

iverilog -g2012 -Wall -o results/qflow_x_sanity_tb.out \
  tb/tb_qflow_x_sanity.v \
  rtl/fdpe_kernel.v \
  rtl/skag_weight_kernel.v \
  rtl/path_selector_kernel.v \
  rtl/qflow_cloud_kernel.v \
  2>&1 | tee results/x_sanity_compile.log

vvp results/qflow_x_sanity_tb.out | tee results/x_sanity_log.txt

grep -i "X SANITY PASS" results/x_sanity_log.txt

python3 - <<'PY'
from pathlib import Path
import pandas as pd
import re

expected_total = 215
root = Path('.')
errors = []
log_path = root / 'results/x_sanity_log.txt'
compile_log_path = root / 'results/x_sanity_compile.log'
out_path = root / 'results/x_sanity_output.csv'
golden_path = root / 'vectors/golden_vectors.csv'

log = log_path.read_text(errors='ignore') if log_path.exists() else ''
compile_log = compile_log_path.read_text(errors='ignore') if compile_log_path.exists() else ''

if 'X SANITY PASS' not in log:
    errors.append('Simulation log does not contain X SANITY PASS')
if re.search(r'FAIL_X_SANITY|X SANITY FAILED', log):
    errors.append('Simulation log contains X sanity failure')
if re.search(r'\bx\b|\bz\b', log, re.IGNORECASE):
    # Do not fail on words like X_SANITY; focus on dumped binary tokens in failure lines.
    if 'FAIL_X_SANITY' in log:
        errors.append('Simulation log contains X/Z failure diagnostics')

if not out_path.exists():
    errors.append('Missing results/x_sanity_output.csv')
else:
    xs = pd.read_csv(out_path)
    if len(xs) != expected_total:
        errors.append(f'Expected {expected_total} X-sanity output rows, got {len(xs)}')
    for col in ['selected_path_id', 'best_weight', 'bottleneck_fidelity', 'latency_cycles', 'status_flags']:
        bad = xs[col].astype(str).str.contains(r'[xXzZ]', regex=True).any()
        if bad:
            errors.append(f'Column {col} contains X/Z text')
            break
    latencies = sorted(set(int(x) for x in xs['latency_cycles'])) if len(xs) else []
    if latencies != [2]:
        errors.append(f'Expected latency_cycles [2], got {latencies}')

if not golden_path.exists():
    errors.append('Missing vectors/golden_vectors.csv')
else:
    golden = pd.read_csv(golden_path)
    if len(golden) != expected_total:
        errors.append(f'Expected {expected_total} golden rows, got {len(golden)}')
    if out_path.exists():
        xs = pd.read_csv(out_path)
        merged = golden.merge(xs, on='test_id', suffixes=('_golden', '_hw'))
        if len(merged) != expected_total:
            errors.append(f'Expected {expected_total} merged rows, got {len(merged)}')
        else:
            mismatches = []
            for _, r in merged.iterrows():
                if int(r['expected_selected_path_id']) != int(r['selected_path_id']):
                    mismatches.append((r['test_id'], 'selected_path_id'))
                    break
                if int(r['expected_best_weight']) != int(r['best_weight']):
                    mismatches.append((r['test_id'], 'best_weight'))
                    break
                if int(r['expected_bottleneck_fidelity']) != int(r['bottleneck_fidelity']):
                    mismatches.append((r['test_id'], 'bottleneck_fidelity'))
                    break
                flags = int(r['status_flags'])
                done = flags & 1
                valid = (flags >> 1) & 1
                no_path = (flags >> 2) & 1
                exp_valid = int(r['expected_valid_path'])
                if done != 1:
                    mismatches.append((r['test_id'], 'done_status'))
                    break
                if exp_valid and not valid:
                    mismatches.append((r['test_id'], 'valid_status'))
                    break
                if (not exp_valid) and not no_path:
                    mismatches.append((r['test_id'], 'no_path_status'))
                    break
            if mismatches:
                errors.append(f'Golden/output mismatch: {mismatches[0]}')

if errors:
    print('X/Z output-sanity audit FAILED')
    for e in errors:
        print(' -', e)
    raise SystemExit(1)

snap = root / 'results/evidence_snapshot_05_x_sanity_pass'
snap.mkdir(parents=True, exist_ok=True)
for src_name in [
    'results/x_sanity_compile.log',
    'results/x_sanity_log.txt',
    'results/x_sanity_output.csv',
    'vectors/golden_vectors.csv',
    'vectors/exp_lut.hex',
]:
    src = root / src_name
    dst = snap / Path(src_name).name
    if src.exists():
        dst.write_bytes(src.read_bytes())

xs = pd.read_csv(out_path)
valid_dist = pd.read_csv(golden_path)['expected_valid_path'].value_counts().to_dict()
readme = f"""# QFlow Cloud FPGA Kernel — Evidence Snapshot 05

This snapshot records Hardcore Local Check Step 4 before AWS EC2 F2 launch.

## Result

- Golden vectors reused/regenerated: {expected_total}
- X/Z output-sanity transaction rows: {len(xs)}
- RTL compile with `iverilog -Wall`: PASS
- RTL simulation: PASS
- Output ports checked for unknown/high-impedance values: PASS
- Golden value/status consistency: PASS
- Latency cycles observed in transaction rows: {sorted(set(int(x) for x in xs['latency_cycles']))}
- Expected-valid distribution: {valid_dist}

## Coverage purpose

This step checks that observable top-level outputs remain fully driven and deterministic after reset, after start, at done, and after done deassertion. It also rechecks selected path, score, bottleneck fidelity, latency, and status flags against the fixed-seed golden-vector dataset.

## Claim boundary

This is still local RTL simulation evidence only. It is not AWS F2 physical FPGA execution evidence yet.
"""
(snap / 'README.md').write_text(readme)

print('X/Z output-sanity audit PASS')
print(f'Golden vectors: {expected_total}')
print(f'X-sanity output rows: {len(xs)}')
print(f'Latency cycles observed: {sorted(set(int(x) for x in xs["latency_cycles"]))}')
print(f'Snapshot written: {snap}')
PY

echo "STEP 4 PASS: X/Z output-sanity local regression is clean."
