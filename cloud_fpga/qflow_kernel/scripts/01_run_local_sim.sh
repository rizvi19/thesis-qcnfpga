#!/usr/bin/env bash
set -euo pipefail

# Run from repository root or from cloud_fpga/qflow_kernel.
if [[ -d "cloud_fpga/qflow_kernel" ]]; then
  cd cloud_fpga/qflow_kernel
fi

command -v python3 >/dev/null || { echo "python3 missing"; exit 1; }
command -v iverilog >/dev/null || { echo "iverilog missing. Install: sudo apt update && sudo apt install -y iverilog"; exit 1; }
command -v vvp >/dev/null || { echo "vvp missing. Install Icarus Verilog."; exit 1; }

make all

echo "Local QFlow cloud-kernel simulation PASS. Do not launch AWS before this passes."
