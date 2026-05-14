// ============================================================================
// QFlow Pareto Comparator C0 — Full Metric Comparator
//
// Purpose:
//   Standalone ASIC/VLSI study kernel for comparing two candidate routes.
//
// Candidate metrics:
//   score      : lower is better
//   fidelity   : higher is better
//   key_count  : higher is better
//   hop_count  : lower is better
//   qber       : lower is better
//
// Pareto dominance:
//   A dominates B if A is no worse in all metrics and strictly better in
//   at least one metric.
// ============================================================================

`timescale 1ns/1ps

module pareto_cmp_c0_full #(
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
    output reg tie,
    output reg a_dominates_b,
    output reg b_dominates_a
);

    wire a_no_worse;
    wire b_no_worse;
    wire a_strict_better;
    wire b_strict_better;

    assign a_no_worse =
        (score_a     <= score_b)     &&
        (fidelity_a  >= fidelity_b)  &&
        (key_count_a >= key_count_b) &&
        (hop_count_a <= hop_count_b) &&
        (qber_a      <= qber_b);

    assign b_no_worse =
        (score_b     <= score_a)     &&
        (fidelity_b  >= fidelity_a)  &&
        (key_count_b >= key_count_a) &&
        (hop_count_b <= hop_count_a) &&
        (qber_b      <= qber_a);

    assign a_strict_better =
        (score_a     < score_b)     ||
        (fidelity_a  > fidelity_b)  ||
        (key_count_a > key_count_b) ||
        (hop_count_a < hop_count_b) ||
        (qber_a      < qber_b);

    assign b_strict_better =
        (score_b     < score_a)     ||
        (fidelity_b  > fidelity_a)  ||
        (key_count_b > key_count_a) ||
        (hop_count_b < hop_count_a) ||
        (qber_b      < qber_a);

    wire a_dom_comb = a_no_worse && a_strict_better;
    wire b_dom_comb = b_no_worse && b_strict_better;

    // Tie-break policy if no Pareto dominance:
    // 1. lower score
    // 2. higher fidelity
    // 3. higher key_count
    // 4. lower hop_count
    // 5. lower qber
    wire a_tiebreak =
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

    wire exact_tie =
        (score_a == score_b) &&
        (fidelity_a == fidelity_b) &&
        (key_count_a == key_count_b) &&
        (hop_count_a == hop_count_b) &&
        (qber_a == qber_b);

    always @(posedge clk) begin
        if (!rst_n) begin
            done          <= 1'b0;
            select_a      <= 1'b0;
            select_b      <= 1'b0;
            tie           <= 1'b0;
            a_dominates_b <= 1'b0;
            b_dominates_a <= 1'b0;
        end else begin
            done <= start;

            if (start) begin
                a_dominates_b <= a_dom_comb;
                b_dominates_a <= b_dom_comb;
                tie           <= exact_tie;

                if (exact_tie) begin
                    select_a <= 1'b0;
                    select_b <= 1'b0;
                end else if (a_dom_comb) begin
                    select_a <= 1'b1;
                    select_b <= 1'b0;
                end else if (b_dom_comb) begin
                    select_a <= 1'b0;
                    select_b <= 1'b1;
                end else if (a_tiebreak) begin
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
