# QFlow Pareto-C0 first physical-design constraint file
# Auto-generated from RTL port declarations

set clk_name clk
set clk_period 10.000

create_clock -name core_clock -period $clk_period [get_ports $clk_name]

set_input_delay 1.000 -clock core_clock [get_ports start]
set_input_delay 1.000 -clock core_clock [get_ports {score_a[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {fidelity_a[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {key_count_a[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {hop_count_a[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {qber_a[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {score_b[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {fidelity_b[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {key_count_b[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {hop_count_b[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {qber_b[*]}]

set_output_delay 1.000 -clock core_clock [get_ports done]
set_output_delay 1.000 -clock core_clock [get_ports select_a]
set_output_delay 1.000 -clock core_clock [get_ports select_b]
set_output_delay 1.000 -clock core_clock [get_ports tie]
set_output_delay 1.000 -clock core_clock [get_ports a_dominates_b]
set_output_delay 1.000 -clock core_clock [get_ports b_dominates_a]

set_false_path -from [get_ports rst_n]
