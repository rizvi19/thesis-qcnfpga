# QFlow Cloud FPGA Kernel — Evidence Snapshot 05

This snapshot records Hardcore Local Check Step 4 before AWS EC2 F2 launch.

## Result

- Golden vectors reused/regenerated: 215
- X/Z output-sanity transaction rows: 215
- RTL compile with `iverilog -Wall`: PASS
- RTL simulation: PASS
- Output ports checked for unknown/high-impedance values: PASS
- Golden value/status consistency: PASS
- Latency cycles observed in transaction rows: [2]
- Expected-valid distribution: {0: 128, 1: 87}

## Coverage purpose

This step checks that observable top-level outputs remain fully driven and deterministic after reset, after start, at done, and after done deassertion. It also rechecks selected path, score, bottleneck fidelity, latency, and status flags against the fixed-seed golden-vector dataset.

## Claim boundary

This is still local RTL simulation evidence only. It is not AWS F2 physical FPGA execution evidence yet.
