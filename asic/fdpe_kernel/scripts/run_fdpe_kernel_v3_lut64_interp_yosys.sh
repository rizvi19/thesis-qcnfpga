#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

mkdir -p asic/fdpe_kernel/results asic/fdpe_kernel/reports

yosys -s asic/fdpe_kernel/scripts/synth_fdpe_kernel_v3_lut64_interp_yosys.ys \
  | tee asic/fdpe_kernel/reports/fdpe_kernel_v3_lut64_interp_yosys_synth.log

cp asic/fdpe_kernel/results/fdpe_kernel_v3_lut64_interp_synth_netlist.v \
   asic/fdpe_kernel/reports/fdpe_kernel_v3_lut64_interp_synth_netlist.v

echo "[PASS] FDPE kernel V3 LUT64 interpolation Yosys synthesis completed."
