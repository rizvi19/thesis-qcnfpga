#!/usr/bin/env bash
set -euo pipefail

mkdir -p results/phase9b

vivado -mode batch -source tcl/run_top_synth.tcl | tee results/phase9b/vivado_top_synth.log

python tools/summarize_top_synth.py \
  --util results/phase9b/qflow_top_synth_utilization.rpt \
  --timing results/phase9b/qflow_top_synth_timing_summary.rpt \
  --out-json results/phase9b/qflow_top_synth_summary.json \
  --out-md results/phase9b/qflow_top_synth_summary.md

echo "Step 9B top-level synthesis complete."
echo " - results/phase9b/vivado_top_synth.log"
echo " - results/phase9b/qflow_top_synth_utilization.rpt"
echo " - results/phase9b/qflow_top_synth_timing_summary.rpt"
echo " - results/phase9b/qflow_top_synth_summary.json"
echo " - results/phase9b/qflow_top_synth_summary.md"
