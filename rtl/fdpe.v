`timescale 1ns/1ps

module fdpe #(
    parameter integer LUT_ENTRIES = 256,
    parameter integer X_BITS      = 17,   // unsigned Q4.13 normalised x input
    parameter integer X_FRAC_BITS = 13,
    parameter integer F_BITS      = 16,
    parameter integer PIPE_STAGES = 3,
    parameter        LUT_FILE    = "results/phase1/exp_lut.hex"
) (
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 valid_i,
    input  wire [X_BITS-1:0]    x_q4_13_i,
    input  wire [F_BITS-1:0]    f_init_q016_i,
    output reg                  valid_o,
    output reg  [F_BITS-1:0]    fidelity_q016_o
);

    localparam integer LUT_STEP_SHIFT = X_FRAC_BITS - 5;  // 13 - 5 = 8
    localparam integer X_EIGHT_Q4_13 = (8 << X_FRAC_BITS); // 8.0 in Q4.13 = 65536

    reg [15:0] lut_mem [0:LUT_ENTRIES-1];

    initial begin
        $display("[FDPE] Loading LUT from %s", LUT_FILE);
        $readmemh(LUT_FILE, lut_mem);
    end

    // -------------------------------
    // Stage 0: clamp / address decode
    // -------------------------------
    reg                 s0_valid;
    reg                 s0_endpoint_zero;
    reg [7:0]           s0_idx;
    reg [7:0]           s0_frac;
    reg [15:0]          s0_f_init;

    // For Q4.13 input and LUT step 1/32, the LUT address is floor(x * 32) = x_q4_13_i >> 8.
    // Because x is clamped to [0,8), valid indices are 0..255 and correspond to bits [15:8].
    // The lower 8 bits are the interpolation fraction within the interval.
    wire [7:0] idx_w  = x_q4_13_i[15:8];
    wire [7:0] frac_w = x_q4_13_i[7:0];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s0_valid         <= 1'b0;
            s0_endpoint_zero <= 1'b0;
            s0_idx           <= 8'd0;
            s0_frac          <= 8'd0;
            s0_f_init        <= 16'd0;
        end else begin
            s0_valid  <= valid_i;
            s0_f_init <= f_init_q016_i;
            if (valid_i) begin
                if (x_q4_13_i >= X_EIGHT_Q4_13) begin
                    s0_endpoint_zero <= 1'b1;
                    s0_idx           <= 8'd0;
                    s0_frac          <= 8'd0;
                end else begin
                    s0_endpoint_zero <= 1'b0;
                    s0_idx           <= idx_w;
                    s0_frac          <= frac_w;
                end
            end
        end
    end

    // Combinational interpolation based on stage-0 registers
    wire [15:0] lut_y0_w = lut_mem[s0_idx];
    wire [15:0] lut_y1_w = (s0_idx == 8'hFF) ? lut_mem[s0_idx] : lut_mem[s0_idx + 8'd1];
    wire signed [17:0] diff_w   = $signed({1'b0, lut_y1_w}) - $signed({1'b0, lut_y0_w});
    wire signed [25:0] prod_w   = diff_w * $signed({1'b0, s0_frac});
    wire signed [17:0] interp_w = (prod_w >= 0)
                                  ? ($signed({1'b0, lut_y0_w}) + ((prod_w + 26'sd128) >>> 8))
                                  : ($signed({1'b0, lut_y0_w}) + ((prod_w - 26'sd128) >>> 8));

    // -------------------------------
    // Stage 1: register decay result
    // -------------------------------
    reg                 s1_valid;
    reg                 s1_endpoint_zero;
    reg [15:0]          s1_f_init;
    reg [15:0]          s1_decay;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s1_valid         <= 1'b0;
            s1_endpoint_zero <= 1'b0;
            s1_f_init        <= 16'd0;
            s1_decay         <= 16'd0;
        end else begin
            s1_valid         <= s0_valid;
            s1_endpoint_zero <= s0_endpoint_zero;
            s1_f_init        <= s0_f_init;
            if (s0_valid) begin
                if (s0_endpoint_zero)
                    s1_decay <= 16'd0;
                else if (interp_w < 0)
                    s1_decay <= 16'd0;
                else if (interp_w > 18'sd65535)
                    s1_decay <= 16'hFFFF;
                else
                    s1_decay <= interp_w[15:0];
            end
        end
    end

    // -------------------------------
    // Stage 2: multiply by F_init and scale back to Q0.16
    // -------------------------------
    reg                s2_valid;
    reg [15:0]         s2_result;
    integer            div_tmp;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s2_valid        <= 1'b0;
            s2_result       <= 16'd0;
            valid_o         <= 1'b0;
            fidelity_q016_o <= 16'd0;
        end else begin
            s2_valid <= s1_valid;
            if (s1_valid) begin
                div_tmp = ((s1_f_init * s1_decay) + 32'd32767) / 32'd65535;
                if (s1_endpoint_zero)
                    s2_result <= 16'd0;
                else if (div_tmp < 0)
                    s2_result <= 16'd0;
                else if (div_tmp > 65535)
                    s2_result <= 16'hFFFF;
                else
                    s2_result <= div_tmp[15:0];
            end

            valid_o         <= s2_valid;
            fidelity_q016_o <= s2_result;
        end
    end

endmodule
