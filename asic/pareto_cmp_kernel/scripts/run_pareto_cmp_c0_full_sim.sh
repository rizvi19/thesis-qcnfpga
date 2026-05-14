#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

mkdir -p asic/pareto_cmp_kernel/results

iverilog -g2012 \
  -o asic/pareto_cmp_kernel/results/pareto_cmp_c0_full_tb.out \
  asic/pareto_cmp_kernel/tb/tb_pareto_cmp_c0_full.v \
  asic/pareto_cmp_kernel/src/pareto_cmp_c0_full.v

vvp asic/pareto_cmp_kernel/results/pareto_cmp_c0_full_tb.out \
  | tee asic/pareto_cmp_kernel/results/pareto_cmp_c0_full_sim_output.txt

grep -q "PARETO_CMP_C0_FULL_SIM_PASS" \
  asic/pareto_cmp_kernel/results/pareto_cmp_c0_full_sim_output.txt

echo "[PASS] Pareto comparator C0 simulation completed."
