// ============================================================================
// QFlow FDPE Kernel V3 — 64-entry LUT with linear interpolation
// Standalone ASIC/VLSI study kernel
//
// Difference from V1:
//   V2: 128-entry LUT + interpolation
//   V2: 128-entry LUT + linear interpolation
//
// Function:
//   y0 = LUT[index]
//   y1 = LUT[index + 1]
//   interp = y0 + frac * (y1 - y0) / 256
//   fidelity_out = f_init * interp
//
// Fixed-point:
//   f_init_q016     : Q0.16
//   LUT values      : Q0.16
//   frac_q08        : Q0.8 fraction between y0 and y1
//   fidelity_q016   : Q0.16
//
// Research purpose:
//   Test whether 64-entry LUT + interpolation gives acceptable accuracy with
//   acceptable generic synthesis cost.
// ============================================================================

`timescale 1ns/1ps

module fdpe_kernel_v3_lut64_interp #(
    parameter FID_W = 16,
    parameter IDX_W = 6,
    parameter FRAC_W = 8
)(
    input  wire                  clk,
    input  wire                  rst_n,

    input  wire                  start,
    input  wire [FID_W-1:0]       f_init_q016,
    input  wire [IDX_W-1:0]       lut_index,
    input  wire [FRAC_W-1:0]      frac_q08,

    output reg                   done,
    output reg  [FID_W-1:0]       fidelity_q016
);

    reg [FID_W-1:0] exp_lut [0:63];

    initial begin
        $readmemh("asic/fdpe_kernel/config/exp_lut_64.hex", exp_lut);
    end

    // Stage 1: read y0/y1 and capture inputs
    reg [FID_W-1:0] f_init_s1;
    reg [FID_W-1:0] y0_s1;
    reg [FID_W-1:0] y1_s1;
    reg [FRAC_W-1:0] frac_s1;
    reg valid_s1;

    // Stage 2: interpolation
    reg [FID_W-1:0] f_init_s2;
    reg [FID_W-1:0] interp_s2;
    reg valid_s2;

    // Stage 3: fidelity multiply
    reg [31:0] mult_s3;
    reg valid_s3;

    wire [IDX_W-1:0] next_index;
    assign next_index = (lut_index == 6'd63) ? 6'd63 : (lut_index + 6'd1);

    // signed difference y1 - y0
    reg signed [16:0] diff_s2_comb;
    reg signed [25:0] frac_mult_s2_comb;
    reg signed [17:0] interp_s2_comb;

    always @(posedge clk) begin
        if (!rst_n) begin
            f_init_s1     <= {FID_W{1'b0}};
            y0_s1         <= {FID_W{1'b0}};
            y1_s1         <= {FID_W{1'b0}};
            frac_s1       <= {FRAC_W{1'b0}};
            valid_s1      <= 1'b0;

            f_init_s2     <= {FID_W{1'b0}};
            interp_s2     <= {FID_W{1'b0}};
            valid_s2      <= 1'b0;

            mult_s3       <= 32'd0;
            valid_s3      <= 1'b0;

            fidelity_q016 <= {FID_W{1'b0}};
            done          <= 1'b0;
        end else begin
            // Stage 1
            valid_s1  <= start;
            f_init_s1 <= f_init_q016;
            y0_s1     <= exp_lut[lut_index];
            y1_s1     <= exp_lut[next_index];
            frac_s1   <= frac_q08;

            // Stage 2: interp = y0 + ((frac * (y1-y0)) >> 8)
            valid_s2  <= valid_s1;
            f_init_s2 <= f_init_s1;

            diff_s2_comb = $signed({1'b0, y1_s1}) - $signed({1'b0, y0_s1});
            frac_mult_s2_comb = diff_s2_comb * $signed({1'b0, frac_s1});
            interp_s2_comb = $signed({1'b0, y0_s1}) + (frac_mult_s2_comb >>> FRAC_W);

            if (interp_s2_comb < 0)
                interp_s2 <= 16'd0;
            else if (interp_s2_comb > 18'sd65535)
                interp_s2 <= 16'd65535;
            else
                interp_s2 <= interp_s2_comb[15:0];

            // Stage 3
            valid_s3 <= valid_s2;
            mult_s3  <= f_init_s2 * interp_s2;

            // Output
            done <= valid_s3;
            if (valid_s3) begin
                fidelity_q016 <= mult_s3[31:16];
            end
        end
    end

endmodule
