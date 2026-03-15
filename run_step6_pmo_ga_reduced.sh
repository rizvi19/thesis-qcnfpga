#!/usr/bin/env bash
set -euo pipefail

mkdir -p sim results/phase4 tb

python tools/generate_pmo_ga_reduced_vectors.py --out-dir results/phase4 --tb-dir tb

iverilog -g2012 -o sim/pmo_ga_reduced_tb.out   rtl/ga_pareto_cmp.v   rtl/ga_select.v   rtl/ga_elitism.v   rtl/pmo_ga_reduced.v   tb/tb_pmo_ga_reduced.v

vvp sim/pmo_ga_reduced_tb.out   +VECTORS=tb/pmo_ga_reduced_candidates.memh   +LOG=results/phase4/pmo_ga_reduced_sim_results.csv   +SUMMARY=results/phase4/pmo_ga_reduced_sim_summary.txt

python tools/pmo_ga_log_to_json.py   --summary-txt results/phase4/pmo_ga_reduced_sim_summary.txt   --csv results/phase4/pmo_ga_reduced_sim_results.csv   --out results/phase4/pmo_ga_reduced_sim_summary.json

echo "Step 6A reduced PMO-GA flow complete."
echo " - results/phase4/pmo_ga_reduced_candidates.csv"
echo " - results/phase4/pmo_ga_reduced_expected.json"
echo " - results/phase4/pmo_ga_reduced_sim_results.csv"
echo " - results/phase4/pmo_ga_reduced_sim_summary.txt"
echo " - results/phase4/pmo_ga_reduced_sim_summary.json"
