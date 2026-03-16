#!/usr/bin/env bash
set -euo pipefail
mkdir -p results/phase9h tb sim

# Re-run the tc5 smoke so implementation is always attached to a known-good functional baseline.
python tools/generate_top_tc5_vectors.py --out-dir results/phase9h --tb-dir tb
iverilog -g2012 -o sim/qflow_top_tc5_tb.out rtl/fdpe_tc5.v rtl/xorshift128plus.v rtl/ga_pareto_cmp.v rtl/ga_select.v rtl/ga_elitism.v rtl/ga_crossover.v rtl/ga_mutate.v rtl/pmo_ga_multigen.v rtl/skag_mem_tc4.v rtl/qflow_top_tc5.v tb/tb_qflow_top_tc5.v
vvp sim/qflow_top_tc5_tb.out +VECTORS=tb/qflow_top_tc5_candidates.memh +LOG=results/phase9h/qflow_top_tc5_smoke_results.csv +SUMMARY=results/phase9h/qflow_top_tc5_smoke_summary.txt
python tools/qflow_top_tc5_log_to_json.py --csv results/phase9h/qflow_top_tc5_smoke_results.csv --out results/phase9h/qflow_top_tc5_smoke_summary.json

vivado -mode batch -source tcl/run_top_tc5_impl.tcl | tee results/phase9h/vivado_top_tc5_impl.log
python tools/summarize_top_tc5_impl.py \
  --timing-rpt results/phase9h/qflow_top_tc5_impl_timing_summary.rpt \
  --util-rpt results/phase9h/qflow_top_tc5_impl_utilization.rpt \
  --route-status-rpt results/phase9h/qflow_top_tc5_impl_route_status.rpt \
  --out-json results/phase9h/qflow_top_tc5_impl_summary.json \
  --out-md results/phase9h/qflow_top_tc5_impl_summary.md

printf "Step 9H post-route implementation complete.\n"
printf " - results/phase9h/qflow_top_tc5_smoke_summary.json\n"
printf " - results/phase9h/vivado_top_tc5_impl.log\n"
printf " - results/phase9h/qflow_top_tc5_impl_summary.json\n"
printf " - results/phase9h/qflow_top_tc5_impl_summary.md\n"
