// ============================================================================
// QFlow Pareto Comparator C1 — Score-First Practical Selector
//
// Purpose:
//   Lower-area practical route-candidate selector.
//
// Difference from C0:
//   C0 computes full Pareto dominance plus tie-break.
//   C1 uses priority-ordered comparison only.
//
// Priority:
//   1. lower score
//   2. higher fidelity
//   3. higher key_count
//   4. lower hop_count
//   5. lower qber
//
// Candidate metrics:
//   score      : lower is better
//   fidelity   : higher is better
//   key_count  : higher is better
//   hop_count  : lower is better
//   qber       : lower is better
// ============================================================================

`timescale 1ns/1ps

module pareto_cmp_c1_scorefirst #(
    parameter SCORE_W = 32,
    parameter FID_W   = 16,
    parameter KEY_W   = 16,
    parameter HOP_W   = 8,
    parameter QBER_W  = 16
)(
    input wire clk,
    input wire rst_n,
    input wire start,

    input wire [SCORE_W-1:0] score_a,
    input wire [FID_W-1:0]   fidelity_a,
    input wire [KEY_W-1:0]   key_count_a,
    input wire [HOP_W-1:0]   hop_count_a,
    input wire [QBER_W-1:0]  qber_a,

    input wire [SCORE_W-1:0] score_b,
    input wire [FID_W-1:0]   fidelity_b,
    input wire [KEY_W-1:0]   key_count_b,
    input wire [HOP_W-1:0]   hop_count_b,
    input wire [QBER_W-1:0]  qber_b,

    output reg done,
    output reg select_a,
    output reg select_b,
    output reg tie
);

    wire exact_tie =
        (score_a == score_b) &&
        (fidelity_a == fidelity_b) &&
        (key_count_a == key_count_b) &&
        (hop_count_a == hop_count_b) &&
        (qber_a == qber_b);

    wire a_wins =
        (score_a < score_b) ? 1'b1 :
        (score_a > score_b) ? 1'b0 :
        (fidelity_a > fidelity_b) ? 1'b1 :
        (fidelity_a < fidelity_b) ? 1'b0 :
        (key_count_a > key_count_b) ? 1'b1 :
        (key_count_a < key_count_b) ? 1'b0 :
        (hop_count_a < hop_count_b) ? 1'b1 :
        (hop_count_a > hop_count_b) ? 1'b0 :
        (qber_a < qber_b) ? 1'b1 :
        1'b0;

    always @(posedge clk) begin
        if (!rst_n) begin
            done     <= 1'b0;
            select_a <= 1'b0;
            select_b <= 1'b0;
            tie      <= 1'b0;
        end else begin
            done <= start;

            if (start) begin
                tie <= exact_tie;

                if (exact_tie) begin
                    select_a <= 1'b0;
                    select_b <= 1'b0;
                end else if (a_wins) begin
                    select_a <= 1'b1;
                    select_b <= 1'b0;
                end else begin
                    select_a <= 1'b0;
                    select_b <= 1'b1;
                end
            end
        end
    end

endmodule
