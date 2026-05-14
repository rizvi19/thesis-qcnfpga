###############################################################################
# Created by write_sdc
###############################################################################
current_design fdpe_kernel_v3_lut64_interp
###############################################################################
# Timing Constraints
###############################################################################
create_clock -name core_clock -period 10.0000 [get_ports {clk}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {f_init_q016[0]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {f_init_q016[10]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {f_init_q016[11]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {f_init_q016[12]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {f_init_q016[13]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {f_init_q016[14]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {f_init_q016[15]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {f_init_q016[1]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {f_init_q016[2]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {f_init_q016[3]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {f_init_q016[4]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {f_init_q016[5]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {f_init_q016[6]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {f_init_q016[7]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {f_init_q016[8]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {f_init_q016[9]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {frac_q08[0]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {frac_q08[1]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {frac_q08[2]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {frac_q08[3]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {frac_q08[4]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {frac_q08[5]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {frac_q08[6]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {frac_q08[7]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {lut_index[0]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {lut_index[1]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {lut_index[2]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {lut_index[3]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {lut_index[4]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {lut_index[5]}]
set_input_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {start}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {done}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {fidelity_q016[0]}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {fidelity_q016[10]}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {fidelity_q016[11]}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {fidelity_q016[12]}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {fidelity_q016[13]}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {fidelity_q016[14]}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {fidelity_q016[15]}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {fidelity_q016[1]}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {fidelity_q016[2]}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {fidelity_q016[3]}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {fidelity_q016[4]}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {fidelity_q016[5]}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {fidelity_q016[6]}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {fidelity_q016[7]}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {fidelity_q016[8]}]
set_output_delay 1.0000 -clock [get_clocks {core_clock}] -add_delay [get_ports {fidelity_q016[9]}]
set_false_path\
    -from [get_ports {rst_n}]
###############################################################################
# Environment
###############################################################################
###############################################################################
# Design Rules
###############################################################################
