#!/usr/bin/env bash
set -euo pipefail

mkdir -p results/phase10_latency sim/obj_dir results/paper/export/pdf results/paper/export/svg results/paper/export/png

echo "=== Step 10A: Hardware latency benchmark ==="
iverilog -g2012 -s tb_qflow_top_tc5_latency \
  -o sim/obj_dir/tb_qflow_top_tc5_latency.vvp \
  rtl/xorshift128plus.v \
  rtl/fdpe_tc5.v \
  rtl/skag_mem_tc4.v \
  rtl/ga_init.v \
  rtl/ga_fitness.v \
  rtl/ga_pareto_cmp.v \
  rtl/ga_select.v \
  rtl/ga_elitism.v \
  rtl/ga_crossover.v \
  rtl/ga_mutate.v \
  rtl/ga_controller.v \
  rtl/pmo_ga_reduced.v \
  rtl/pmo_ga_family.v \
  rtl/pmo_ga_multigen.v \
  rtl/qflow_top_tc5.v \
  tb/tb_qflow_top_tc5_latency.v

vvp sim/obj_dir/tb_qflow_top_tc5_latency.vvp \
  +VECTORS=tb/qflow_top_tc_candidates.memh \
  +SUMMARY=results/phase10_latency/qflow_top_tc5_latency_summary.txt \
  +CSV=results/phase10_latency/qflow_top_tc5_latency_metrics.csv

echo
echo "=== Step 10A: Software latency benchmark ==="
python3 tools/benchmark_sw_latency.py \
  --out-csv results/phase10_latency/sw_latency_benchmark.csv \
  --out-json results/phase10_latency/sw_latency_benchmark.json

echo
echo "=== Step 10A: Prepare canonical FIG02 CSV ==="
python3 tools/prepare_fig02_latency_summary.py \
  --hw-summary results/phase10_latency/qflow_top_tc5_latency_summary.txt \
  --sw-csv results/phase10_latency/sw_latency_benchmark.csv \
  --out results/paper/data/figures/fig02_latency/source/latency_summary.csv

echo
echo "Done."
echo "Hardware summary: results/phase10_latency/qflow_top_tc5_latency_summary.txt"
echo "Software summary: results/phase10_latency/sw_latency_benchmark.csv"
echo "Canonical FIG02 CSV: results/paper/data/figures/fig02_latency/source/latency_summary.csv"
