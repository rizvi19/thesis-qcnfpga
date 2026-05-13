# QFlow Cloud FPGA Kernel — Local PASS Snapshot 01

This snapshot records the first local simulation pass before launching AWS EC2 F2.

## Result

- Golden vectors generated successfully.
- Testbench generated successfully.
- RTL compiled using Icarus Verilog.
- RTL simulation passed.
- Hardware-output CSV matched Python golden vectors.
- PASS = 3
- FAIL = 0

## Tested cases

1. T001_normal_ring6
2. T002_blocked_candidate
3. T003_high_threshold

## Current measured RTL simulation result

The kernel selected the expected path, score, bottleneck fidelity, and latency-cycle outputs for all generated golden vectors.

## Claim boundary

This is local RTL simulation evidence only. It is not yet AWS F2 physical FPGA execution evidence.
