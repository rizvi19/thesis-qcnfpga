#!/usr/bin/env bash
set -euo pipefail

OUTDIR="results/phase10d"
mkdir -p "$OUTDIR"

python3 tools/evaluate_qflow_baselines_phase10d_selection_sweep.py \
  --topologies mesh9 mesh16 irregular12 \
  --seed-start 42 \
  --repetitions 6 \
  --ga-pop-size 64 \
  --ga-max-generations 100 \
  --out-json "$OUTDIR/qflow_baseline_eval_phase10d_selection_sweep.json" \
  --out-csv  "$OUTDIR/qflow_baseline_eval_phase10d_selection_sweep.csv" \
  --out-md   "$OUTDIR/qflow_baseline_eval_phase10d_selection_sweep.md"

echo "Wrote $OUTDIR/qflow_baseline_eval_phase10d_selection_sweep.json"
echo "Wrote $OUTDIR/qflow_baseline_eval_phase10d_selection_sweep.csv"
echo "Wrote $OUTDIR/qflow_baseline_eval_phase10d_selection_sweep.md"
