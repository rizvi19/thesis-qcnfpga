# QFlow Cloud FPGA Kernel — Hardcore Local Check Plan

## Gate policy

AWS EC2 F2 must not be launched until all local gates pass.

## Step 1: Extended deterministic regression

Target: replace the original 3-vector smoke test with 15 deterministic vectors.

Coverage:

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

Pass condition:

- `make all` passes.
- `results/local_sim_output.txt` contains `ALL TESTS PASS`.
- `results/hardware_vs_python.csv` contains only PASS rows.
- exactly 15 golden vectors are generated.
- exactly 15 hardware-output rows are generated.
- latency_cycles is stable at 2 for this starter local wrapper.
- no_path status is correctly asserted for the no-valid-path vector.

## Later gates

Step 2: randomized fixed-seed regression.
Step 3: unknown/X-output and reset/start pulse stress.
Step 4: Verilator lint or stricter compile gate.
Step 5: AWS register-map wrapper readiness.
Step 6: build artifact/evidence manifest.
