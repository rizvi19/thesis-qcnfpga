# QFlow SKAG-W1 first physical-design constraint file
# OpenROAD-compatible SDC version

set clk_name clk
set clk_period 10.000

create_clock -name core_clock -period $clk_period [get_ports $clk_name]

# Explicit input delays. Avoid remove_from_collection because this OpenROAD/STA
# environment does not support it in the current flow context.
set_input_delay 1.000 -clock core_clock [get_ports start]
set_input_delay 1.000 -clock core_clock [get_ports {key_count[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {avg_fidelity_q016[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {arrival_rate_q88[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {qber_q016[*]}]

set_output_delay 1.000 -clock core_clock [get_ports done]
set_output_delay 1.000 -clock core_clock [get_ports {score_q16[*]}]

# Treat reset as asynchronous control for this first implementation.
set_false_path -from [get_ports rst_n]
