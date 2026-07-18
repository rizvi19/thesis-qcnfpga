`timescale 1ns / 1ps

// Synthesis-only transparent wrapper for the frozen P4 controller.
// It adds no state or behavior and exposes every reviewed controller port.
module rl_controller_synth_top (
    input  wire        clk,
    input  wire        rst,
    input  wire        start,
    input  wire        input_valid,
    input  wire        no_path_in,
    input  wire [15:0] min_key_occupancy_u16,
    input  wire [15:0] bottleneck_fidelity_u16,
    input  wire [15:0] offered_request_load_u16,
    input  wire [15:0] utilization_imbalance_u16,
    output wire        ready,
    output wire        busy,
    output wire        done,
    output wire        output_valid,
    output wire        invalid_state,
    output wire        stall,
    output wire        no_path_out,
    output wire [7:0]  state_id,
    output wire [1:0]  proposed_action,
    output wire [1:0]  selected_action,
    output wire [17:0] profile_payload,
    output wire        switched,
    output wire [1:0]  dwell_count_sat
);

    rl_controller controller_i (
        .clk(clk),
        .rst(rst),
        .start(start),
        .input_valid(input_valid),
        .no_path_in(no_path_in),
        .min_key_occupancy_u16(min_key_occupancy_u16),
        .bottleneck_fidelity_u16(bottleneck_fidelity_u16),
        .offered_request_load_u16(offered_request_load_u16),
        .utilization_imbalance_u16(utilization_imbalance_u16),
        .ready(ready),
        .busy(busy),
        .done(done),
        .output_valid(output_valid),
        .invalid_state(invalid_state),
        .stall(stall),
        .no_path_out(no_path_out),
        .state_id(state_id),
        .proposed_action(proposed_action),
        .selected_action(selected_action),
        .profile_payload(profile_payload),
        .switched(switched),
        .dwell_count_sat(dwell_count_sat)
    );

endmodule
