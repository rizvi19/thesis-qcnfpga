# QFlow Cloud FPGA Kernel — Evidence Snapshot 07

This snapshot records Hardcore Local Check Step 6 before AWS EC2 F2 launch.

## Result

- AWS-style local MMIO/register wrapper simulation: PASS
- Golden vectors used: 215
- MMIO transactions compared against Python golden vectors: 215
- Icarus Verilog `-Wall` compile/elaboration: PASS
- MMIO hardware-output CSV vs Python golden CSV: PASS
- Verilator MMIO lint: see `verilator_mmio_status.txt`
- Yosys MMIO generic synthesis: see `yosys_mmio_status.txt`

## Claim boundary

This is still local register-wrapper simulation/static-check evidence only. It is not AWS F2 physical FPGA execution evidence yet.

The wrapper is a local stand-in for the future AWS CL/OCL/MMIO attachment. It proves that the QFlow cloud kernel can be controlled through a host-style register map before paid F2 time is used.
