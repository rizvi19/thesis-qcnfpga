# Gate 6 — AWS Register-Map Wrapper Readiness

Gate 6 adds a local host-style register wrapper around the already-hardened QFlow cloud kernel.

## Why this gate exists

AWS F2 execution will eventually involve host software writing input registers, starting the kernel, polling status, and reading output registers. Debugging that transaction style directly on AWS wastes money. Gate 6 checks it locally first.

## Pass criteria

- 215 golden vectors are regenerated.
- The MMIO testbench is generated from `golden_vectors.csv`.
- `qflow_mmio_regs` compiles with Icarus Verilog `-Wall`.
- The MMIO simulation prints `MMIO WRAPPER PASS`.
- `mmio_output.csv` matches the Python golden vectors with 215 PASS and 0 FAIL.
- Optional Verilator lint and Yosys generic synthesis are run if installed.
- Evidence is saved in `results/evidence_snapshot_07_mmio_wrapper_pass/`.

## Claim boundary

Gate 6 is still local simulation/static evidence only. It is not AWS F2 physical FPGA evidence.
