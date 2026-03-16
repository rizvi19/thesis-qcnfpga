set outdir "results/phase9h"
file mkdir $outdir
set partname "xc7a200tfbg484-1"
create_project qflow_top_tc5_impl_proj $outdir/qflow_top_tc5_impl_proj -part $partname -force
set_property target_language Verilog [current_project]
set_property XPM_LIBRARIES {XPM_MEMORY} [current_project]
foreach f [list \
    rtl/fdpe_tc5.v \
    rtl/xorshift128plus.v \
    rtl/ga_pareto_cmp.v \
    rtl/ga_select.v \
    rtl/ga_elitism.v \
    rtl/ga_crossover.v \
    rtl/ga_mutate.v \
    rtl/pmo_ga_multigen.v \
    rtl/skag_mem_tc4.v \
    rtl/qflow_top_tc5.v ] {
    read_verilog -sv $f
}
read_xdc xdc/qflow_top_tc5.xdc

synth_design -top qflow_top_tc5 -part $partname
write_checkpoint -force $outdir/qflow_top_tc5_impl_synth.dcp
report_utilization -hierarchical -hierarchical_depth 3 -file $outdir/qflow_top_tc5_impl_synth_utilization.rpt
report_timing_summary -delay_type max -report_unconstrained -check_timing_verbose -max_paths 20 -file $outdir/qflow_top_tc5_impl_synth_timing_summary.rpt

opt_design -directive Explore
write_checkpoint -force $outdir/qflow_top_tc5_impl_opt.dcp

place_design -directive Explore
phys_opt_design -directive Explore
write_checkpoint -force $outdir/qflow_top_tc5_impl_place.dcp
report_utilization -file $outdir/qflow_top_tc5_impl_place_utilization.rpt
report_clock_utilization -file $outdir/qflow_top_tc5_impl_clock_utilization.rpt
report_timing_summary -delay_type max -report_unconstrained -check_timing_verbose -max_paths 20 -file $outdir/qflow_top_tc5_impl_place_timing_summary.rpt

route_design -directive Explore
phys_opt_design -post_route -directive AggressiveExplore
write_checkpoint -force $outdir/qflow_top_tc5_impl_route.dcp

report_utilization -file $outdir/qflow_top_tc5_impl_utilization.rpt
report_timing_summary -delay_type max -report_unconstrained -check_timing_verbose -max_paths 30 -file $outdir/qflow_top_tc5_impl_timing_summary.rpt
report_timing -delay_type max -max_paths 20 -sort_by group -file $outdir/qflow_top_tc5_impl_critical_paths.rpt
report_route_status -file $outdir/qflow_top_tc5_impl_route_status.rpt
report_drc -file $outdir/qflow_top_tc5_impl_drc.rpt
report_power -file $outdir/qflow_top_tc5_impl_power.rpt

close_project
exit
