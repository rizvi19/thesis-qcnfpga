set outdir "results/phase8b"
file mkdir $outdir

set partname "xc7a200tfbg484-1"

proc run_ooc {top files outdir partname} {
    create_project ${top}_ooc $outdir/${top}_proj -part $partname -force
    # Keep project language as Verilog; SystemVerilog parsing is enabled per file via read_verilog -sv.
    set_property target_language Verilog [current_project]
    foreach f $files {
        read_verilog -sv $f
    }
    synth_design -top $top -part $partname -mode out_of_context
    report_utilization -file $outdir/${top}_utilization.rpt
    report_timing_summary -file $outdir/${top}_timing_summary.rpt
    close_project
}

run_ooc fdpe [list rtl/fdpe.v] $outdir $partname
run_ooc skag_mem [list rtl/skag_mem.v] $outdir $partname
run_ooc xorshift128plus [list rtl/xorshift128plus.v] $outdir $partname
run_ooc pmo_ga_multigen [list rtl/ga_pareto_cmp.v rtl/ga_select.v rtl/ga_elitism.v rtl/ga_crossover.v rtl/ga_mutate.v rtl/pmo_ga_multigen.v] $outdir $partname

exit
