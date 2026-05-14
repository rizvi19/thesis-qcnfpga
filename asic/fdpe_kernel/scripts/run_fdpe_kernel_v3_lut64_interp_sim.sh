#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

mkdir -p asic/fdpe_kernel/results

iverilog -g2012 \
  -o asic/fdpe_kernel/results/fdpe_kernel_v3_lut64_interp_tb.out \
  asic/fdpe_kernel/tb/tb_fdpe_kernel_v3_lut64_interp.v \
  asic/fdpe_kernel/src/fdpe_kernel_v3_lut64_interp.v

vvp asic/fdpe_kernel/results/fdpe_kernel_v3_lut64_interp_tb.out \
  | tee asic/fdpe_kernel/results/fdpe_kernel_v3_lut64_interp_sim_output.txt

grep -q "FDPE_KERNEL_V3_LUT64_INTERP_SIM_PASS" \
  asic/fdpe_kernel/results/fdpe_kernel_v3_lut64_interp_sim_output.txt

echo "[PASS] FDPE kernel V3 LUT64 interpolation simulation completed."
