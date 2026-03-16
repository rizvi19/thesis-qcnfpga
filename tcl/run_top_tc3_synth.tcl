set outdir "results/phase9e"
file mkdir $outdir
set partname "xc7a200tfbg484-1"
create_project qflow_top_tc3_proj $outdir/qflow_top_tc3_proj -part $partname -force
set_property target_language Verilog [current_project]
set_property XPM_LIBRARIES {XPM_MEMORY} [current_project]
foreach f [list     rtl/fdpe.v     rtl/xorshift128plus.v     rtl/ga_pareto_cmp.v     rtl/ga_select.v     rtl/ga_elitism.v     rtl/ga_crossover.v     rtl/ga_mutate.v     rtl/pmo_ga_multigen.v     rtl/skag_mem_tc3.v     rtl/qflow_top_tc3.v ] {
    read_verilog -sv $f
}
read_xdc xdc/qflow_top_tc3.xdc
synth_design -top qflow_top_tc3 -part $partname
report_utilization -hierarchical -hierarchical_depth 3 -file $outdir/qflow_top_tc3_utilization.rpt
report_timing_summary -delay_type max -report_unconstrained -check_timing_verbose -max_paths 20 -file $outdir/qflow_top_tc3_timing_summary.rpt
report_timing -delay_type max -max_paths 10 -sort_by group -file $outdir/qflow_top_tc3_critical_paths.rpt
write_checkpoint -force $outdir/qflow_top_tc3_synth.dcp
close_project
exit
