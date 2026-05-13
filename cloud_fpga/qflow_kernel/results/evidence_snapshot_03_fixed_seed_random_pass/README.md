# QFlow Cloud FPGA Kernel — Evidence Snapshot 03

This snapshot records Hardcore Local Check Step 2 before AWS EC2 F2 launch.

## Result

- Deterministic vectors: 15
- Fixed-seed randomized vectors: 200
- Total vectors: 215
- RTL compile: PASS
- RTL simulation: PASS
- Hardware-output CSV vs Python golden CSV: PASS
- PASS rows: 215
- FAIL rows: 0
- Latency cycles observed in local wrapper: [2]
- Expected-valid distribution: {0: 128, 1: 87}

## Coverage purpose

This step stress-tests the small QFlow cloud kernel under fixed-seed randomized combinations of edge validity, key scarcity, fidelity threshold, decay index, QBER, arrival-rate bucket, distance/cost, invalid edge IDs, zero-length candidates, valid-path outputs, and no-path outputs.

## Claim boundary

This is still local RTL simulation evidence only. It is not AWS F2 physical FPGA execution evidence yet.
