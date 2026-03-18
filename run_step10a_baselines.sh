#!/usr/bin/env bash
set -euo pipefail

mkdir -p results/phase10a

python3 tools/evaluate_qflow_baselines.py \
  --topologies ring6 \
  --out-json results/phase10a/qflow_baseline_eval_phase10a.json \
  --out-csv  results/phase10a/qflow_baseline_eval_phase10a.csv \
  --out-md   results/phase10a/qflow_baseline_eval_phase10a.md

printf "Step 10A baseline evaluation complete.\n"
printf " - results/phase10a/qflow_baseline_eval_phase10a.json\n"
printf " - results/phase10a/qflow_baseline_eval_phase10a.csv\n"
printf " - results/phase10a/qflow_baseline_eval_phase10a.md\n"
