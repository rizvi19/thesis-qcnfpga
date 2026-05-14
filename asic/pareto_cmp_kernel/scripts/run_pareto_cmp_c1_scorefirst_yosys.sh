#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

mkdir -p asic/pareto_cmp_kernel/results asic/pareto_cmp_kernel/reports

yosys -s asic/pareto_cmp_kernel/scripts/synth_pareto_cmp_c1_scorefirst_yosys.ys \
  | tee asic/pareto_cmp_kernel/reports/pareto_cmp_c1_scorefirst_yosys_synth.log

cp asic/pareto_cmp_kernel/results/pareto_cmp_c1_scorefirst_synth_netlist.v \
   asic/pareto_cmp_kernel/reports/pareto_cmp_c1_scorefirst_synth_netlist.v

echo "[PASS] Pareto comparator C1 score-first Yosys synthesis completed."
