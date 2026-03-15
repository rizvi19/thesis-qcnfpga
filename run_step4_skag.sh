#!/usr/bin/env bash
set -euo pipefail

mkdir -p results/phase2 tb sim

python tools/generate_skag_vectors.py --out-dir results/phase2 --tb-dir tb
iverilog -g2012 -o sim/skag_tb.out rtl/skag_mem.v tb/tb_skag.v
vvp sim/skag_tb.out \
  +VECTORS=tb/skag_vectors.memh \
  +LOG=results/phase2/skag_sim_results.csv \
  +SUMMARY=results/phase2/skag_sim_summary.txt
python tools/skag_log_to_json.py --csv results/phase2/skag_sim_results.csv --out results/phase2/skag_sim_summary.json

echo "Step 4 SKAG flow complete."
echo " - results/phase2/skag_golden_vectors.csv"
echo " - results/phase2/skag_vector_summary.json"
echo " - results/phase2/skag_sim_results.csv"
echo " - results/phase2/skag_sim_summary.txt"
echo " - results/phase2/skag_sim_summary.json"
