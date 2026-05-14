#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

mkdir -p asic/fdpe_kernel/results asic/fdpe_kernel/reports

yosys -s asic/fdpe_kernel/scripts/synth_fdpe_kernel_v1_lut128_yosys.ys \
  | tee asic/fdpe_kernel/reports/fdpe_kernel_v1_lut128_yosys_synth.log

cp asic/fdpe_kernel/results/fdpe_kernel_v1_lut128_synth_netlist.v \
   asic/fdpe_kernel/reports/fdpe_kernel_v1_lut128_synth_netlist.v

echo "[PASS] FDPE kernel V1 LUT128 Yosys synthesis completed."
