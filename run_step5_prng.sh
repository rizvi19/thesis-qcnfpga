#!/usr/bin/env bash
set -euo pipefail
mkdir -p sim results/phase3
python tools/verify_randomness.py --help >/dev/null
iverilog -g2012 -o sim/xorshift_tb.out rtl/xorshift128plus.v tb/tb_xorshift.v
vvp sim/xorshift_tb.out +DUMP=results/phase3/xorshift_dump.txt +SUMMARY=results/phase3/xorshift_tb_summary.txt
python tools/verify_randomness.py --dump results/phase3/xorshift_dump.txt --out results/phase3/xorshift_randomness.json
echo "Step 5 PRNG flow complete."
echo " - results/phase3/xorshift_dump.txt"
echo " - results/phase3/xorshift_tb_summary.txt"
echo " - results/phase3/xorshift_randomness.json"
