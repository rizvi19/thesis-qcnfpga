set outdir "results/phase9h_ooc"
set partname "xc7a200tfbg484-1"

open_checkpoint $outdir/qflow_top_tc5_impl_ooc_place.dcp

# Resume from the successful placed checkpoint. The previous run already showed
# that place_design and pre-route phys_opt completed cleanly.
route_design -directive Explore

# In Vivado 2024.2 the earlier '-post_route' option caused the batch run to stop.
# The routed design already met timing, so finalize reports directly from the
# routed checkpoint.
write_checkpoint -force $outdir/qflow_top_tc5_impl_ooc_route.dcp

report_utilization -file $outdir/qflow_top_tc5_impl_ooc_utilization.rpt
report_clock_utilization -file $outdir/qflow_top_tc5_impl_ooc_clock_utilization.rpt
report_timing_summary -delay_type max -report_unconstrained -check_timing_verbose -max_paths 30 -file $outdir/qflow_top_tc5_impl_ooc_timing_summary.rpt
report_timing -delay_type max -max_paths 20 -sort_by group -file $outdir/qflow_top_tc5_impl_ooc_critical_paths.rpt
report_route_status -file $outdir/qflow_top_tc5_impl_ooc_route_status.rpt
report_drc -file $outdir/qflow_top_tc5_impl_ooc_drc.rpt
report_power -file $outdir/qflow_top_tc5_impl_ooc_power.rpt

close_design
exit
