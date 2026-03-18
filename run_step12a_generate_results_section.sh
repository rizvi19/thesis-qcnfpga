#!/usr/bin/env bash
set -euo pipefail
mkdir -p results/phase12a
python3 tools/generate_phase12a_results_section.py
echo "Generated:"
echo " - results/phase12a/qflow_thesis_results_section.md"
echo " - results/phase12a/qflow_thesis_results_section.tex"
echo " - results/phase12a/qflow_results_tables.csv"
echo " - results/phase12a/qflow_results_highlights.json"
