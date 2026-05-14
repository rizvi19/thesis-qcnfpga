// ============================================================================
// QFlow SKAG Weight Kernel W1 — Shift-Add Fixed-Alpha Edge Score
//
// Purpose:
//   Optimized ASIC/VLSI study kernel for SKAG edge scoring.
//
// Difference from W0:
//   W0 uses runtime alpha multipliers.
//   W1 freezes alpha weights and implements them using shift-add logic.
//
// Fixed alpha interpretation:
//   alpha_k = 256 = 1.0
//   alpha_f = 384 = 1.5
//   alpha_l = 128 = 0.5
//   alpha_q = 512 = 2.0
//
// Score model:
//   score =
//       key_shortage
//     + fidelity_penalty
//     + (fidelity_penalty >> 1)
//     + (arrival_penalty >> 1)
//     + (qber << 1)
//
// Lower score means better edge.
// ============================================================================

`timescale 1ns/1ps

module skag_weight_w1_shiftadd #(
    parameter KEY_W   = 16,
    parameter FID_W   = 16,
    parameter RATE_W  = 16,
    parameter QBER_W  = 16,
    parameter SCORE_W = 32
)(
    input  wire                  clk,
    input  wire                  rst_n,

    input  wire                  start,

    input  wire [KEY_W-1:0]       key_count,
    input  wire [FID_W-1:0]       avg_fidelity_q016,
    input  wire [RATE_W-1:0]      arrival_rate_q88,
    input  wire [QBER_W-1:0]      qber_q016,

    output reg                   done,
    output reg  [SCORE_W-1:0]     score_q16
);

    localparam [15:0] TARGET_KEY_COUNT   = 16'd256;
    localparam [15:0] MAX_FIDELITY       = 16'hFFFF;
    localparam [15:0] TARGET_ARRIVAL_Q88 = 16'h0100; // 1.0 in Q8.8

    wire [15:0] key_shortage;
    wire [15:0] fidelity_penalty;
    wire [15:0] arrival_penalty;
    wire [15:0] qber_penalty;

    assign key_shortage =
        (key_count >= TARGET_KEY_COUNT) ? 16'd0 : (TARGET_KEY_COUNT - key_count);

    assign fidelity_penalty =
        (avg_fidelity_q016 >= MAX_FIDELITY) ? 16'd0 : (MAX_FIDELITY - avg_fidelity_q016);

    assign arrival_penalty =
        (arrival_rate_q88 >= TARGET_ARRIVAL_Q88) ? 16'd0 : (TARGET_ARRIVAL_Q88 - arrival_rate_q88);

    assign qber_penalty = qber_q016;

    // Stage 1: capture weighted terms using shift-add only.
    reg [31:0] term_k_s1;
    reg [31:0] term_f_s1;
    reg [31:0] term_l_s1;
    reg [31:0] term_q_s1;
    reg        valid_s1;

    // Stage 2: sum.
    reg [33:0] sum_s2;
    reg        valid_s2;

    always @(posedge clk) begin
        if (!rst_n) begin
            term_k_s1 <= 32'd0;
            term_f_s1 <= 32'd0;
            term_l_s1 <= 32'd0;
            term_q_s1 <= 32'd0;
            valid_s1  <= 1'b0;

            sum_s2    <= 34'd0;
            valid_s2  <= 1'b0;

            score_q16 <= {SCORE_W{1'b0}};
            done      <= 1'b0;
        end else begin
            // Stage 1: fixed-alpha shift-add score terms.
            valid_s1 <= start;

            // alpha_k = 1.0
            term_k_s1 <= {16'd0, key_shortage};

            // alpha_f = 1.5 = 1 + 0.5
            term_f_s1 <= {16'd0, fidelity_penalty}
                       + {17'd0, fidelity_penalty[15:1]};

            // alpha_l = 0.5
            term_l_s1 <= {17'd0, arrival_penalty[15:1]};

            // alpha_q = 2.0
            term_q_s1 <= {15'd0, qber_penalty, 1'b0};

            // Stage 2
            valid_s2 <= valid_s1;
            sum_s2   <= {2'b00, term_k_s1}
                      + {2'b00, term_f_s1}
                      + {2'b00, term_l_s1}
                      + {2'b00, term_q_s1};

            done <= valid_s2;

            if (valid_s2) begin
                score_q16 <= sum_s2[31:0];
            end
        end
    end

endmodule
