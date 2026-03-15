#!/usr/bin/env bash
set -euo pipefail

PYTHON=${PYTHON:-python}
IVERILOG=${IVERILOG:-iverilog}
VVP=${VVP:-vvp}

mkdir -p tb sim results/phase1

$PYTHON tools/fdpe_csv_to_mem.py --csv results/phase1/fdpe_golden_vectors.csv --out tb/fdpe_vectors.memh
$IVERILOG -g2012 -o sim/fdpe_tb.out rtl/fdpe.v tb/tb_fdpe.v
$VVP sim/fdpe_tb.out +VECTORS=tb/fdpe_vectors.memh +LOG=results/phase1/fdpe_sim_results.csv +SUMMARY=results/phase1/fdpe_sim_summary.txt
$PYTHON tools/fdpe_log_to_json.py --csv results/phase1/fdpe_sim_results.csv --out results/phase1/fdpe_sim_summary.json

echo "Step 3 FDPE flow complete."
echo " - results/phase1/fdpe_sim_results.csv"
echo " - results/phase1/fdpe_sim_summary.txt"
echo " - results/phase1/fdpe_sim_summary.json"
