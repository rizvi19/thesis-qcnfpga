# QFlow Cloud FPGA Kernel — Evidence Snapshot 06

This snapshot records Hardcore Local Check Step 5 before AWS EC2 F2 launch.

## Result

- Golden vectors regenerated: 215
- Icarus Verilog compile/elaboration with `-Wall`: PASS
- RTL simulation from strict-compiled output: PASS
- Hardware-output CSV vs Python golden CSV: PASS
- Verilator lint: see `verilator_status.txt`
- Yosys generic synthesis: see `yosys_status.txt`

## Claim boundary

This is still local RTL/static-check evidence only. It is not AWS F2 physical FPGA execution evidence yet.

Yosys generic synthesis, if available, is only a local sanity check. It is not a replacement for AWS HDK/Vivado AFI build.
