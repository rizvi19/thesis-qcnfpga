set_property SRC_FILE_INFO {cfile:/media/shahriar-rizvi/Data/CSE/Thesis/from13March/qflow_step1_phase0/xdc/qflow_top_synth.xdc rfile:../xdc/qflow_top_synth.xdc id:1} [current_design]
set_property SRC_FILE_INFO {cfile:/home/shahriar-rizvi/Work/VLSI/Xilinx/Vivado/2024.2/data/ip/xpm/xpm_memory/tcl/xpm_memory_xdc.tcl rfile:../../../../../../../../home/shahriar-rizvi/Work/VLSI/Xilinx/Vivado/2024.2/data/ip/xpm/xpm_memory/tcl/xpm_memory_xdc.tcl id:2 order:LATE scoped_inst:u_skag/fidelity_mem_xpm unmanaged:yes} [current_design]
set_property src_info {type:XDC file:1 line:2 export:INPUT save:INPUT read:READ} [current_design]
set_input_delay  2.000 -clock clk [remove_from_collection [all_inputs] [get_ports clk]]
current_instance u_skag/fidelity_mem_xpm
set_property src_info {type:SCOPED_XDC file:2 line:55 export:INPUT save:NONE read:READ} [current_design]
set my_var [get_property dram_emb_xdc [get_cells -quiet -hier -filter {PRIMITIVE_SUBGROUP==LUTRAM || PRIMITIVE_SUBGROUP==dram || PRIMITIVE_SUBGROUP==uram || PRIMITIVE_SUBGROUP==BRAM}]]
