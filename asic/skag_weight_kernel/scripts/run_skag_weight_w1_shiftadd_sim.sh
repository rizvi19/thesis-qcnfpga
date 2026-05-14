#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

mkdir -p asic/skag_weight_kernel/results

iverilog -g2012 \
  -o asic/skag_weight_kernel/results/skag_weight_w1_shiftadd_tb.out \
  asic/skag_weight_kernel/tb/tb_skag_weight_w1_shiftadd.v \
  asic/skag_weight_kernel/src/skag_weight_w1_shiftadd.v

vvp asic/skag_weight_kernel/results/skag_weight_w1_shiftadd_tb.out \
  | tee asic/skag_weight_kernel/results/skag_weight_w1_shiftadd_sim_output.txt

grep -q "SKAG_WEIGHT_W1_SHIFTADD_SIM_PASS" \
  asic/skag_weight_kernel/results/skag_weight_w1_shiftadd_sim_output.txt

echo "[PASS] SKAG weight W1 shift-add simulation completed."
