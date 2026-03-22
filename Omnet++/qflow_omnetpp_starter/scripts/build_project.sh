#!/usr/bin/env bash
set -euo pipefail

opp_makemake -f --deep -O out -o qflow_omnetpp_starter
make -j"$(nproc)"
echo "Build complete."
