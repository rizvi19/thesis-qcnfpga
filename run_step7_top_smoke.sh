#!/usr/bin/env bash
set -euo pipefail
mkdir -p sim results/phase7
python tools/generate_top_smoke_vectors.py --out-dir results/phase7 --tb-dir tb
iverilog -g2012 -o sim/qflow_top_smoke_tb.out \
  rtl/fdpe.v \
  rtl/skag_mem.v \
  rtl/xorshift128plus.v \
  rtl/ga_pareto_cmp.v \
  rtl/ga_select.v \
  rtl/ga_elitism.v \
  rtl/ga_crossover.v \
  rtl/ga_mutate.v \
  rtl/pmo_ga_multigen.v \
  rtl/qflow_top_smoke.v \
  tb/tb_qflow_top_smoke.v
vvp sim/qflow_top_smoke_tb.out +VECTORS=tb/qflow_top_candidates.memh +LOG=results/phase7/qflow_top_smoke_sim_results.csv +SUMMARY=results/phase7/qflow_top_smoke_sim_summary.txt
python tools/qflow_top_log_to_json.py --csv results/phase7/qflow_top_smoke_sim_results.csv --out results/phase7/qflow_top_smoke_sim_summary.json
echo "Step 7 top-level smoke flow complete."
echo " - results/phase7/qflow_top_candidates.csv"
echo " - results/phase7/qflow_top_expected.json"
echo " - results/phase7/qflow_top_smoke_sim_results.csv"
echo " - results/phase7/qflow_top_smoke_sim_summary.txt"
echo " - results/phase7/qflow_top_smoke_sim_summary.json"
