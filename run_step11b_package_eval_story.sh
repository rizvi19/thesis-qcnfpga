#!/usr/bin/env bash
set -euo pipefail

mkdir -p results/phase11b
python3 tools/summarize_qflow_eval_after10d.py
echo "Generated:"
echo " - results/phase11b/qflow_eval_story_after10d.json"
echo " - results/phase11b/qflow_eval_story_after10d.csv"
echo " - results/phase11b/qflow_eval_story_after10d.md"
