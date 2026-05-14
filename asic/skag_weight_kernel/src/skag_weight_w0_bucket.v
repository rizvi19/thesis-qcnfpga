// ============================================================================
// QFlow SKAG Weight Kernel W0 — Bucketized Fixed-Point Edge Score
//
// Purpose:
//   Standalone ASIC/VLSI study kernel for SKAG edge scoring.
//
// Score model:
//   score =
//       alpha_k * key_shortage
//     + alpha_f * fidelity_penalty
//     + alpha_l * arrival_penalty
//     + alpha_q * qber
//
// Fixed-point conventions:
//   key_count          : unsigned integer
//   avg_fidelity_q016  : Q0.16
//   arrival_rate_q88   : Q8.8
//   qber_q016          : Q0.16
//   alpha_*            : Q8.8
//   score_q16          : Q16.16-like unsigned score
//
// Notes:
//   - This baseline avoids true division.
//   - Lower score means better edge.
//   - This is a generic synthesis baseline, not final ASIC signoff.
// ============================================================================

`timescale 1ns/1ps

module skag_weight_w0_bucket #(
    parameter KEY_W   = 16,
    parameter FID_W   = 16,
    parameter RATE_W  = 16,
    parameter QBER_W  = 16,
    parameter ALPHA_W = 16,
    parameter SCORE_W = 32
)(
    input  wire                  clk,
    input  wire                  rst_n,

    input  wire                  start,

    input  wire [KEY_W-1:0]       key_count,
    input  wire [FID_W-1:0]       avg_fidelity_q016,
    input  wire [RATE_W-1:0]      arrival_rate_q88,
    input  wire [QBER_W-1:0]      qber_q016,

    input  wire [ALPHA_W-1:0]     alpha_k_q88,
    input  wire [ALPHA_W-1:0]     alpha_f_q88,
    input  wire [ALPHA_W-1:0]     alpha_l_q88,
    input  wire [ALPHA_W-1:0]     alpha_q_q88,

    output reg                   done,
    output reg  [SCORE_W-1:0]     score_q16
);

    // ------------------------------------------------------------------------
    // Targets / constants
    // ------------------------------------------------------------------------
    localparam [15:0] TARGET_KEY_COUNT  = 16'd256;
    localparam [15:0] MAX_FIDELITY      = 16'hFFFF;
    localparam [15:0] TARGET_ARRIVAL_Q88 = 16'h0100; // 1.0 in Q8.8

    // ------------------------------------------------------------------------
    // Penalty terms
    // ------------------------------------------------------------------------
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

    // ------------------------------------------------------------------------
    // Stage 1: weighted products
    // Q8.8 alpha × 16-bit term = 32-bit product
    // ------------------------------------------------------------------------
    reg [31:0] prod_k_s1;
    reg [31:0] prod_f_s1;
    reg [31:0] prod_l_s1;
    reg [31:0] prod_q_s1;
    reg        valid_s1;

    // ------------------------------------------------------------------------
    // Stage 2: sum and scale
    // Divide by 256 to account for Q8.8 alpha scale.
    // ------------------------------------------------------------------------
    reg [33:0] sum_s2;
    reg        valid_s2;

    always @(posedge clk) begin
        if (!rst_n) begin
            prod_k_s1 <= 32'd0;
            prod_f_s1 <= 32'd0;
            prod_l_s1 <= 32'd0;
            prod_q_s1 <= 32'd0;
            valid_s1  <= 1'b0;

            sum_s2    <= 34'd0;
            valid_s2  <= 1'b0;

            score_q16 <= {SCORE_W{1'b0}};
            done      <= 1'b0;
        end else begin
            // Stage 1
            valid_s1  <= start;
            prod_k_s1 <= alpha_k_q88 * key_shortage;
            prod_f_s1 <= alpha_f_q88 * fidelity_penalty;
            prod_l_s1 <= alpha_l_q88 * arrival_penalty;
            prod_q_s1 <= alpha_q_q88 * qber_penalty;

            // Stage 2
            valid_s2 <= valid_s1;
            sum_s2   <= {2'b00, prod_k_s1}
                      + {2'b00, prod_f_s1}
                      + {2'b00, prod_l_s1}
                      + {2'b00, prod_q_s1};

            done <= valid_s2;

            if (valid_s2) begin
                // Scale down Q8.8 alpha multiplication.
                // sum_s2 is 34 bits. After shifting by 8, the useful score
                // fits safely within 32 bits for this W0 bucketized model.
                score_q16 <= {6'd0, sum_s2[33:8]};
            end
        end
    end

endmodule
