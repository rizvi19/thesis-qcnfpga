#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

mkdir -p asic/skag_weight_kernel/results asic/skag_weight_kernel/reports

yosys -s asic/skag_weight_kernel/scripts/synth_skag_weight_w0_bucket_yosys.ys \
  | tee asic/skag_weight_kernel/reports/skag_weight_w0_bucket_yosys_synth.log

cp asic/skag_weight_kernel/results/skag_weight_w0_bucket_synth_netlist.v \
   asic/skag_weight_kernel/reports/skag_weight_w0_bucket_synth_netlist.v

echo "[PASS] SKAG weight W0 bucket Yosys synthesis completed."
