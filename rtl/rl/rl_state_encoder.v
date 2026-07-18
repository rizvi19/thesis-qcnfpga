`timescale 1ns / 1ps

// QFlow-RL P4 frozen state encoder.
// Inputs are unsigned normalized 16-bit codes for the clipped real domain 0..1.
// Equality with a threshold enters the higher bin.
module rl_state_encoder (
    input  wire        clk,
    input  wire        rst,
    input  wire        en,
    input  wire [15:0] min_key_occupancy_u16,
    input  wire [15:0] bottleneck_fidelity_u16,
    input  wire [15:0] offered_request_load_u16,
    input  wire [15:0] utilization_imbalance_u16,
    output reg         valid,
    output reg  [7:0]  state_id
);

    function [1:0] key_or_load_bin;
        input [15:0] value;
        begin
            if (value >= 16'd49151)
                key_or_load_bin = 2'd3;
            else if (value >= 16'd32768)
                key_or_load_bin = 2'd2;
            else if (value >= 16'd16384)
                key_or_load_bin = 2'd1;
            else
                key_or_load_bin = 2'd0;
        end
    endfunction

    function [1:0] fidelity_bin;
        input [15:0] value;
        begin
            if (value >= 16'd62914)
                fidelity_bin = 2'd3;
            else if (value >= 16'd60948)
                fidelity_bin = 2'd2;
            else if (value >= 16'd58982)
                fidelity_bin = 2'd1;
            else
                fidelity_bin = 2'd0;
        end
    endfunction

    function [1:0] imbalance_bin;
        input [15:0] value;
        begin
            if (value >= 16'd32768)
                imbalance_bin = 2'd3;
            else if (value >= 16'd16384)
                imbalance_bin = 2'd2;
            else if (value >= 16'd8192)
                imbalance_bin = 2'd1;
            else
                imbalance_bin = 2'd0;
        end
    endfunction

    always @(posedge clk) begin
        if (rst) begin
            valid    <= 1'b0;
            state_id <= 8'd0;
        end else begin
            valid <= en;
            if (en) begin
                state_id <= {
                    key_or_load_bin(min_key_occupancy_u16),
                    fidelity_bin(bottleneck_fidelity_u16),
                    key_or_load_bin(offered_request_load_u16),
                    imbalance_bin(utilization_imbalance_u16)
                };
            end
        end
    end

endmodule
