#!/usr/bin/env bash
set -euo pipefail
mkdir -p sim results/phase5 tb
python tools/generate_pmo_ga_family_vectors.py --out-dir results/phase5 --tb-dir tb
iverilog -g2012 -o sim/pmo_ga_family_tb.out \
  rtl/ga_pareto_cmp.v rtl/ga_select.v rtl/ga_elitism.v rtl/ga_init.v rtl/ga_fitness.v rtl/ga_crossover.v rtl/ga_mutate.v rtl/ga_controller.v rtl/pmo_ga_family.v tb/tb_pmo_ga_family.v
vvp sim/pmo_ga_family_tb.out +VECTORS=tb/pmo_ga_family_vectors.memh +LOG=results/phase5/pmo_ga_family_sim_results.csv +SUMMARY=results/phase5/pmo_ga_family_sim_summary.txt
python tools/pmo_ga_family_log_to_json.py --summary results/phase5/pmo_ga_family_sim_summary.txt --out results/phase5/pmo_ga_family_sim_summary.json
printf 'Step 6B PMO-GA family flow complete.\n'
printf ' - results/phase5/pmo_ga_family_candidates.csv\n'
printf ' - results/phase5/pmo_ga_family_expected.json\n'
printf ' - results/phase5/pmo_ga_family_sim_results.csv\n'
printf ' - results/phase5/pmo_ga_family_sim_summary.txt\n'
printf ' - results/phase5/pmo_ga_family_sim_summary.json\n'
