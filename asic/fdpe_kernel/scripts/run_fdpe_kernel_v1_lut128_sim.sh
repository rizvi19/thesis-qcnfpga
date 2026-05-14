#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

mkdir -p asic/fdpe_kernel/results

iverilog -g2012 \
  -o asic/fdpe_kernel/results/fdpe_kernel_v1_lut128_tb.out \
  asic/fdpe_kernel/tb/tb_fdpe_kernel_v1_lut128.v \
  asic/fdpe_kernel/src/fdpe_kernel_v1_lut128.v

vvp asic/fdpe_kernel/results/fdpe_kernel_v1_lut128_tb.out \
  | tee asic/fdpe_kernel/results/fdpe_kernel_v1_lut128_sim_output.txt

grep -q "FDPE_KERNEL_V1_LUT128_SIM_PASS" asic/fdpe_kernel/results/fdpe_kernel_v1_lut128_sim_output.txt

echo "[PASS] FDPE kernel V1 LUT128 simulation completed."
