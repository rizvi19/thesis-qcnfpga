# Hardcore Local Check Step 5 — Static lint / elaboration / generic synthesis

This step is a pre-AWS safety gate for the QFlow cloud-FPGA kernel.

## What it checks

1. Regenerates the 215-vector fixed-seed dataset.
2. Regenerates the Verilog testbench.
3. Compiles with `iverilog -g2012 -Wall`.
4. Runs the full simulation and hardware-vs-golden comparison.
5. Runs `verilator --lint-only` if Verilator is installed.
6. Runs a generic Yosys synthesis/elaboration check if Yosys is installed.
7. Creates `results/evidence_snapshot_06_static_lint_pass`.

## Important boundary

This step does not replace AWS Vivado/HDK. It only catches local static RTL problems before paid cloud time.

If Verilator or Yosys is not installed, the script records `SKIP_NOT_INSTALLED` and continues. If they are installed and report fatal errors, the step fails.
