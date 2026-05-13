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
