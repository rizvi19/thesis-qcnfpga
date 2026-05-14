// ============================================================================
// QFlow FDPE Kernel V0
// Standalone ASIC/VLSI study kernel
//
// Function:
//   fidelity_out = f_init * exp_lut[index]
//   where all values are Q0.16 unsigned fixed-point.
//
// Purpose:
//   This is the baseline FDPE kernel for Part C VLSI/ASIC PPA analysis.
//   It is intentionally small, deterministic, and easy to compare against
//   Python/golden vectors.
//
// Evidence boundary:
//   This is an ASIC-study kernel, not a fabricated chip result.
// ============================================================================

`timescale 1ns/1ps

module fdpe_kernel_v0 #(
    parameter FID_W = 16,
    parameter IDX_W = 8
)(
    input  wire                 clk,
    input  wire                 rst_n,

    input  wire                 start,
    input  wire [FID_W-1:0]      f_init_q016,
    input  wire [IDX_W-1:0]      lut_index,

    output reg                  done,
    output reg  [FID_W-1:0]      fidelity_q016
);

    // ------------------------------------------------------------------------
    // 256-entry exp(-x) LUT in Q0.16 format.
    // For V0, we initialize a small representative table procedurally enough
    // for deterministic simulation and synthesis experiments.
    //
    // Later we will replace this with a generated exp_lut_256.hex file.
    // ------------------------------------------------------------------------
    reg [FID_W-1:0] exp_lut [0:255];

    integer i;

    initial begin
        // Coarse hand-filled exponential-like decay table.
        // This is simulation/synthesis-safe. It gives monotonic decreasing
        // values and allows PPA flow testing before using the exact generated LUT.
        for (i = 0; i < 256; i = i + 1) begin
            if (i < 16)
                exp_lut[i] = 16'd65535 - (i * 16'd1900);
            else if (i < 32)
                exp_lut[i] = 16'd35135 - ((i-16) * 16'd1000);
            else if (i < 64)
                exp_lut[i] = 16'd19135 - ((i-32) * 16'd400);
            else if (i < 128)
                exp_lut[i] = 16'd6335 - ((i-64) * 16'd80);
            else if (i < 192)
                exp_lut[i] = 16'd1215 - ((i-128) * 16'd12);
            else
                exp_lut[i] = 16'd447 - ((i-192) * 16'd5);
        end

        // Prevent underflow-like wrap for final region.
        for (i = 240; i < 256; i = i + 1) begin
            exp_lut[i] = 16'd1;
        end
    end

    // ------------------------------------------------------------------------
    // Pipeline registers
    // Stage 1: read LUT and capture f_init
    // Stage 2: multiply and truncate Q0.16 × Q0.16 -> Q0.16
    // ------------------------------------------------------------------------
    reg [FID_W-1:0] f_init_s1;
    reg [FID_W-1:0] exp_s1;
    reg             valid_s1;

    reg [31:0]      mult_s2;
    reg             valid_s2;

    always @(posedge clk) begin
        if (!rst_n) begin
            f_init_s1    <= {FID_W{1'b0}};
            exp_s1       <= {FID_W{1'b0}};
            valid_s1     <= 1'b0;

            mult_s2      <= 32'd0;
            valid_s2     <= 1'b0;

            fidelity_q016 <= {FID_W{1'b0}};
            done          <= 1'b0;
        end else begin
            // Stage 1
            valid_s1  <= start;
            f_init_s1 <= f_init_q016;
            exp_s1    <= exp_lut[lut_index];

            // Stage 2
            valid_s2 <= valid_s1;
            mult_s2  <= f_init_s1 * exp_s1;

            // Output stage
            done <= valid_s2;
            if (valid_s2) begin
                fidelity_q016 <= mult_s2[31:16];
            end
        end
    end

endmodule
