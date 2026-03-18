#!/usr/bin/env bash
set -euo pipefail

mkdir -p results/phase11a

python3 tools/summarize_qflow_for_thesis.py \
  --tc3-json results/phase9e/qflow_top_tc3_synth_summary.json \
  --tc4-json results/phase9f/qflow_top_tc4_synth_summary.json \
  --tc5-json results/phase9g/qflow_top_tc5_synth_summary.json \
  --ooc-json results/phase9h_ooc/qflow_top_tc5_impl_ooc_summary.json \
  --ooc-route-status results/phase9h_ooc/qflow_top_tc5_impl_ooc_route_status.rpt \
  --phase10c-json results/phase10c/qflow_baseline_eval_phase10c_stats.json \
  --out-json results/phase11a/qflow_thesis_packaging_summary.json \
  --out-csv results/phase11a/qflow_thesis_packaging_summary.csv \
  --out-md results/phase11a/qflow_thesis_packaging_summary.md
