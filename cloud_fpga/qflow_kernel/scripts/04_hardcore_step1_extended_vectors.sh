#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[QFlow local hardening step 1] Extended deterministic regression"
echo "Repo subdir: $ROOT"

if ! command -v iverilog >/dev/null 2>&1; then
  echo "ERROR: iverilog not found. Install it first: sudo apt install -y iverilog" >&2
  exit 1
fi
if ! command -v vvp >/dev/null 2>&1; then
  echo "ERROR: vvp not found. Install it first: sudo apt install -y iverilog" >&2
  exit 1
fi

make clean
make all

python3 - <<'PY'
import csv
from pathlib import Path

root = Path('.')
golden = list(csv.DictReader((root/'vectors/golden_vectors.csv').open()))
hw = list(csv.DictReader((root/'results/hardware_output.csv').open()))
comp = list(csv.DictReader((root/'results/hardware_vs_python.csv').open()))
log = (root/'results/local_sim_output.txt').read_text()

expected = 15
assert len(golden) == expected, f"expected {expected} golden vectors, got {len(golden)}"
assert len(hw) == expected, f"expected {expected} hardware rows, got {len(hw)}"
assert len(comp) == expected, f"expected {expected} compare rows, got {len(comp)}"
assert 'ALL TESTS PASS' in log, 'local sim did not report ALL TESTS PASS'
assert 'FAIL ' not in log, 'FAIL found in local simulation log'
assert all(r['pass_fail'] == 'PASS' for r in comp), 'hardware_vs_python contains FAIL rows'

# The starter kernel transaction is intentionally 2 cycles in this local wrapper.
latencies = {int(r['latency_cycles']) for r in hw}
assert latencies == {2}, f"unexpected latency_cycles set: {latencies}"

# Status flag sanity: status_flags = {29'd0, no_path, valid_path, done}.
# For normal valid output, expected decimal is 3. For no_path, expected decimal is 5.
status_by_id = {r['test_id'].strip(): int(r['status_flags']) for r in hw}
assert status_by_id['T005_no_valid_path'] == 5, f"T005 no_path status should be 5, got {status_by_id['T005_no_valid_path']}"
for tid, status in status_by_id.items():
    if tid != 'T005_no_valid_path':
        assert status == 3, f"{tid} valid path status should be 3, got {status}"

print('Extended deterministic regression audit PASS')
print(f'Golden vectors: {len(golden)}')
print(f'Hardware rows: {len(hw)}')
print(f'Compare rows: {len(comp)}')
print(f'Latency cycles observed: {sorted(latencies)}')
PY

SNAP="results/evidence_snapshot_02_extended_local_pass"
mkdir -p "$SNAP"
cp results/local_sim_output.txt "$SNAP/"
cp results/hardware_output.csv "$SNAP/"
cp results/hardware_vs_python.csv "$SNAP/"
cp vectors/golden_vectors.csv "$SNAP/"
cp vectors/exp_lut.hex "$SNAP/"
cat > "$SNAP/README.md" <<'EOF'
# QFlow Cloud FPGA Kernel — Evidence Snapshot 02

This snapshot records the extended deterministic local regression before AWS EC2 F2 launch.

## Result

- Test count: 15 deterministic vectors
- RTL compile: PASS
- RTL simulation: PASS
- Hardware-output CSV vs Python golden CSV: PASS
- Latency cycles observed in local wrapper: 2

## Coverage categories

1. Normal ring-6 path selection
2. Blocked candidate rejection
3. High fidelity-threshold rejection
4. All candidates valid
5. No valid path / no_path assertion
6. Equal-score tie-breaking
7. Low-key-count scarcity penalty
8. Low-fidelity penalty
9. High-QBER penalty
10. Distance/cost penalty
11. Invalid edge ID rejection
12. Zero-length candidate rejection
13. Arrival-rate bucket penalty
14. Zero-decay boundary
15. Maximum-decay boundary

## Claim boundary

This is still local RTL simulation evidence only. It is not AWS F2 physical FPGA execution evidence yet.
EOF

echo "Snapshot written: $SNAP"
echo "STEP 1 PASS: extended deterministic local regression is clean."
