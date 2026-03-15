set outdir "results/phase9a"
file mkdir $outdir
set partname "xc7a200tfbg484-1"

create_project skag_mem_bram_ooc $outdir/skag_mem_bram_proj -part $partname -force
set_property target_language Verilog [current_project]
set_property XPM_LIBRARIES {XPM_MEMORY} [current_project]
read_verilog -sv rtl/skag_mem_bram.v

synth_design -top skag_mem_bram -part $partname -mode out_of_context

# Basic OOC clock so report_timing_summary has a defined period target.
create_clock -name clk -period 10.000 [get_ports clk]

report_utilization   -file $outdir/skag_mem_bram_utilization.rpt
report_timing_summary -file $outdir/skag_mem_bram_timing_summary.rpt

close_project
exit
