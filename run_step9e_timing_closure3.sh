#!/usr/bin/env bash
set -euo pipefail
mkdir -p results/phase9e tb sim
python tools/generate_top_tc3_vectors.py --out-dir results/phase9e --tb-dir tb
iverilog -g2012 -o sim/qflow_top_tc3_tb.out rtl/fdpe.v rtl/xorshift128plus.v rtl/ga_pareto_cmp.v rtl/ga_select.v rtl/ga_elitism.v rtl/ga_crossover.v rtl/ga_mutate.v rtl/pmo_ga_multigen.v rtl/skag_mem_tc3.v rtl/qflow_top_tc3.v tb/tb_qflow_top_tc3.v
vvp sim/qflow_top_tc3_tb.out +VECTORS=tb/qflow_top_tc3_candidates.memh +LOG=results/phase9e/qflow_top_tc3_smoke_results.csv +SUMMARY=results/phase9e/qflow_top_tc3_smoke_summary.txt
python tools/qflow_top_tc3_log_to_json.py --csv results/phase9e/qflow_top_tc3_smoke_results.csv --out results/phase9e/qflow_top_tc3_smoke_summary.json
vivado -mode batch -source tcl/run_top_tc3_synth.tcl | tee results/phase9e/vivado_top_tc3.log
python tools/summarize_top_tc3_synth.py --timing-rpt results/phase9e/qflow_top_tc3_timing_summary.rpt --util-rpt results/phase9e/qflow_top_tc3_utilization.rpt --out-json results/phase9e/qflow_top_tc3_synth_summary.json --out-md results/phase9e/qflow_top_tc3_synth_summary.md
printf "Step 9E timing-closure stage 3 complete.
"
printf " - results/phase9e/qflow_top_tc3_smoke_summary.json
"
printf " - results/phase9e/vivado_top_tc3.log
"
printf " - results/phase9e/qflow_top_tc3_synth_summary.json
"
printf " - results/phase9e/qflow_top_tc3_synth_summary.md
"
