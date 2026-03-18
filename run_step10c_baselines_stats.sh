#!/usr/bin/env bash
set -euo pipefail

OUTDIR="results/phase10c"
mkdir -p "$OUTDIR"

python3 tools/evaluate_qflow_baselines_phase10c_stats.py \
  --topologies mesh9 mesh16 irregular12 \
  --seed-start 42 \
  --repetitions 30 \
  --sim-duration-s 0.5 \
  --tick-dt-s 0.001 \
  --f-min 0.9 \
  --ga-pop-size 64 \
  --ga-max-generations 100 \
  --out-json "$OUTDIR/qflow_baseline_eval_phase10c_stats.json" \
  --out-csv  "$OUTDIR/qflow_baseline_eval_phase10c_stats.csv" \
  --out-md   "$OUTDIR/qflow_baseline_eval_phase10c_stats.md"
