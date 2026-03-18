#!/usr/bin/env bash
set -euo pipefail

mkdir -p results/phase12b
python3 tools/generate_phase12b_writing_assets.py
echo "Generated:"
echo " - results/phase12b/qflow_thesis_results_polished.md"
echo " - results/phase12b/qflow_thesis_results_polished.tex"
echo " - results/phase12b/qflow_paper_results_condensed.md"
echo " - results/phase12b/qflow_paper_results_condensed.tex"
echo " - results/phase12b/qflow_defense_results_bullets.md"
