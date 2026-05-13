`timescale 1ns/1ps
// -----------------------------------------------------------------------------
// QFlow AWS F2 starter kernel - SKAG-style edge scoring
// -----------------------------------------------------------------------------
// Computes a hardware-friendly rank score from key_count, FDPE fidelity,
// arrival-rate bucket, QBER penalty, and distance/cost. Exact reciprocal-heavy
// weights are intentionally avoided in the first AWS run to minimize paid debug
// time and cloud-build timing risk. The claim should be "SKAG-style rank-score
// kernel", not the full canonical SKAG memory subsystem.

module skag_weight_kernel #(
    parameter FID_W    = 16,
    parameter SCORE_W  = 32,
    parameter INF_SCORE = 32'hFFFF_FFFF
)(
    input  wire [15:0] key_count,
    input  wire [FID_W-1:0] fidelity_q016,
    input  wire [15:0] arrival_rate_q8_8,
    input  wire [FID_W-1:0] qber_q016,
    input  wire [SCORE_W-1:0] distance_cost_q16_16,
    input  wire [FID_W-1:0] f_min_threshold,
    output reg  [SCORE_W-1:0] edge_score,
    output wire [FID_W-1:0] edge_fidelity,
    output reg  edge_valid
);
    reg [SCORE_W-1:0] scarcity_penalty;
    reg [SCORE_W-1:0] arrival_penalty;
    reg [SCORE_W-1:0] fidelity_penalty;
    reg [SCORE_W-1:0] qber_penalty;

    assign edge_fidelity = fidelity_q016;

    always @* begin
        edge_valid = (key_count != 16'd0) && (fidelity_q016 >= f_min_threshold);

        if (key_count < 16'd2)
            scarcity_penalty = 32'd32768;
        else if (key_count < 16'd4)
            scarcity_penalty = 32'd16384;
        else if (key_count < 16'd8)
            scarcity_penalty = 32'd8192;
        else
            scarcity_penalty = 32'd4096;

        if (arrival_rate_q8_8 < 16'd512)
            arrival_penalty = 32'd32768;
        else if (arrival_rate_q8_8 < 16'd1024)
            arrival_penalty = 32'd16384;
        else
            arrival_penalty = 32'd8192;

        fidelity_penalty = ({16'd0, (16'hFFFF - fidelity_q016)} << 3);
        qber_penalty     = ({16'd0, qber_q016} << 1);

        if (!edge_valid)
            edge_score = INF_SCORE;
        else
            edge_score = distance_cost_q16_16 + scarcity_penalty + arrival_penalty + fidelity_penalty + qber_penalty;
    end
endmodule
