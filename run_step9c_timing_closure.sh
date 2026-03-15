#!/usr/bin/env bash
set -euo pipefail
mkdir -p results/phase9c tb sim

python tools/generate_top_tc_vectors.py --out-dir results/phase9c --tb-dir tb

iverilog -g2012 -o sim/qflow_top_tc_tb.out \
  rtl/xorshift128plus.v \
  rtl/fdpe.v \
  rtl/ga_pareto_cmp.v \
  rtl/ga_select.v \
  rtl/ga_elitism.v \
  rtl/ga_crossover.v \
  rtl/ga_mutate.v \
  rtl/pmo_ga_multigen.v \
  rtl/skag_mem_tc.v \
  rtl/qflow_top_tc.v \
  tb/tb_qflow_top_tc.v

vvp sim/qflow_top_tc_tb.out \
  +VECTORS=tb/qflow_top_tc_candidates.memh \
  +LOG=results/phase9c/qflow_top_tc_smoke_results.csv \
  +SUMMARY=results/phase9c/qflow_top_tc_smoke_summary.txt

python tools/qflow_top_tc_log_to_json.py \
  --csv results/phase9c/qflow_top_tc_smoke_results.csv \
  --out results/phase9c/qflow_top_tc_smoke_summary.json

vivado -mode batch -source tcl/run_top_tc_synth.tcl | tee results/phase9c/vivado_top_tc.log

python tools/summarize_top_tc_synth.py \
  --timing-rpt results/phase9c/qflow_top_tc_timing_summary.rpt \
  --util-rpt results/phase9c/qflow_top_tc_utilization.rpt \
  --out-json results/phase9c/qflow_top_tc_synth_summary.json \
  --out-md results/phase9c/qflow_top_tc_synth_summary.md

echo "Step 9C timing-closure flow complete."
echo " - results/phase9c/qflow_top_tc_smoke_summary.json"
echo " - results/phase9c/vivado_top_tc.log"
echo " - results/phase9c/qflow_top_tc_synth_summary.json"
echo " - results/phase9c/qflow_top_tc_synth_summary.md"
