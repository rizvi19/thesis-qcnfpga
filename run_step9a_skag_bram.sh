#!/usr/bin/env bash
set -euo pipefail

mkdir -p results/phase9a tb sim rtl tools tcl

python tools/generate_skag_bram_vectors.py --out-dir results/phase9a --tb-dir tb

iverilog -g2012 -o sim/skag_bram_tb.out rtl/skag_mem_bram.v tb/tb_skag_bram.v
vvp sim/skag_bram_tb.out \
  +VECTORS=tb/skag_bram_vectors.memh \
  +LOG=results/phase9a/skag_bram_sim_results.csv \
  +SUMMARY=results/phase9a/skag_bram_sim_summary.txt

python tools/skag_bram_log_to_json.py \
  --csv results/phase9a/skag_bram_sim_results.csv \
  --out results/phase9a/skag_bram_sim_summary.json

if command -v vivado >/dev/null 2>&1; then
  vivado -mode batch \
    -source tcl/run_skag_bram_ooc.tcl \
    -log results/phase9a/vivado_skag_bram_ooc.log \
    -jou results/phase9a/vivado_skag_bram_ooc.jou
else
  echo "Vivado not found. Skipping OOC synthesis."
fi

python tools/summarize_skag_bram_compare.py \
  --baseline-summary results/phase8b/ooc_report_summary.json \
  --optimized-util results/phase9a/skag_mem_bram_utilization.rpt \
  --out-json results/phase9a/skag_bram_compare.json \
  --out-md results/phase9a/skag_bram_compare.md

echo "Step 9A SKAG BRAM optimization flow complete."
echo " - results/phase9a/skag_bram_golden_vectors.csv"
echo " - results/phase9a/skag_bram_vector_summary.json"
echo " - results/phase9a/skag_bram_sim_results.csv"
echo " - results/phase9a/skag_bram_sim_summary.txt"
echo " - results/phase9a/skag_bram_sim_summary.json"
echo " - results/phase9a/skag_bram_compare.json"
echo " - results/phase9a/skag_bram_compare.md"
