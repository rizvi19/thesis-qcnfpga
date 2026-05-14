# QFlow FDPE-V3 first physical-design constraint file
# OpenROAD-compatible SDC version

set clk_name clk
set clk_period 10.000

create_clock -name core_clock -period $clk_period [get_ports $clk_name]

# Explicit input delays.
set_input_delay 1.000 -clock core_clock [get_ports start]
set_input_delay 1.000 -clock core_clock [get_ports {f_init_q016[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {lut_index[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {frac_q08[*]}]

set_output_delay 1.000 -clock core_clock [get_ports done]
set_output_delay 1.000 -clock core_clock [get_ports {fidelity_q016[*]}]

# Treat reset as asynchronous control for this first implementation.
set_false_path -from [get_ports rst_n]
