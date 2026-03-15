#!/usr/bin/env bash
set -euo pipefail
mkdir -p results/phase9d tb sim
python tools/generate_top_tc2_vectors.py --out-dir results/phase9d --tb-dir tb
iverilog -g2012 -o sim/qflow_top_tc2_tb.out rtl/fdpe.v rtl/xorshift128plus.v rtl/ga_pareto_cmp.v rtl/ga_select.v rtl/ga_elitism.v rtl/ga_crossover.v rtl/ga_mutate.v rtl/pmo_ga_multigen.v rtl/skag_mem_tc2.v rtl/qflow_top_tc2.v tb/tb_qflow_top_tc2.v
vvp sim/qflow_top_tc2_tb.out +VECTORS=tb/qflow_top_tc2_candidates.memh +LOG=results/phase9d/qflow_top_tc2_smoke_results.csv +SUMMARY=results/phase9d/qflow_top_tc2_smoke_summary.txt
python tools/qflow_top_tc2_log_to_json.py --csv results/phase9d/qflow_top_tc2_smoke_results.csv --out results/phase9d/qflow_top_tc2_smoke_summary.json
vivado -mode batch -source tcl/run_top_tc2_synth.tcl | tee results/phase9d/vivado_top_tc2.log
python tools/summarize_top_tc2_synth.py --timing-rpt results/phase9d/qflow_top_tc2_timing_summary.rpt --util-rpt results/phase9d/qflow_top_tc2_utilization.rpt --out-json results/phase9d/qflow_top_tc2_synth_summary.json --out-md results/phase9d/qflow_top_tc2_synth_summary.md
printf "Step 9D timing-closure stage 2 complete.
"
printf " - results/phase9d/qflow_top_tc2_smoke_summary.json
"
printf " - results/phase9d/vivado_top_tc2.log
"
printf " - results/phase9d/qflow_top_tc2_synth_summary.json
"
printf " - results/phase9d/qflow_top_tc2_synth_summary.md
"
