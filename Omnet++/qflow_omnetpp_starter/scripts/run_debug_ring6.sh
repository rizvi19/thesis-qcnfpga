#!/usr/bin/env bash
set -euo pipefail

if [[ ! -x ./qflow_omnetpp_starter ]]; then
  echo "Binary not found. Building first..."
  ./scripts/build_project.sh
fi

./qflow_omnetpp_starter -u Cmdenv -c Ring6KeyAwareDebug omnetpp.ini
echo "Wrote results/ring6_keyaware_debug.csv"
