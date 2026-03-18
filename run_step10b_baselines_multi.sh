#!/usr/bin/env bash
set -euo pipefail

mkdir -p results/phase10b

python3 tools/evaluate_qflow_baselines_phase10b.py \
  --topologies mesh9 mesh16 irregular12 \
  --seed 42 \
  --sim-duration-s 0.5 \
  --tick-dt-s 0.001 \
  --f-min 0.9 \
  --ga-pop-size 64 \
  --ga-max-generations 100 \
  --out-json results/phase10b/qflow_baseline_eval_phase10b.json \
  --out-csv  results/phase10b/qflow_baseline_eval_phase10b.csv \
  --out-md   results/phase10b/qflow_baseline_eval_phase10b.md
