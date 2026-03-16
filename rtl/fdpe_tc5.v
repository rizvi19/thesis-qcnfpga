`timescale 1ns/1ps

module fdpe_tc5 #(
    parameter integer LUT_ENTRIES = 256,
    parameter integer X_BITS      = 17,   // unsigned Q4.13 normalised x input
    parameter integer X_FRAC_BITS = 13,
    parameter integer F_BITS      = 16,
    parameter integer PIPE_STAGES = 5,
    parameter        LUT_FILE     = "results/phase1/exp_lut.hex"
) (
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 valid_i,
    input  wire [X_BITS-1:0]    x_q4_13_i,
    input  wire [F_BITS-1:0]    f_init_q016_i,
    output reg                  valid_o,
    output reg  [F_BITS-1:0]    fidelity_q016_o
);

    localparam integer X_EIGHT_Q4_13 = (8 << X_FRAC_BITS); // 8.0 in Q4.13 = 65536

    reg [15:0] lut_mem [0:LUT_ENTRIES-1];

    initial begin
        $display("[FDPE_TC5] Loading LUT from %s", LUT_FILE);
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

    // -------------------------------
    // Stage 1: capture LUT outputs
    // -------------------------------
    reg                 s1_valid;
    reg                 s1_endpoint_zero;
    reg [7:0]           s1_frac;
    reg [15:0]          s1_f_init;
    reg [15:0]          s1_y0;
    reg [15:0]          s1_y1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s1_valid         <= 1'b0;
            s1_endpoint_zero <= 1'b0;
            s1_frac          <= 8'd0;
            s1_f_init        <= 16'd0;
            s1_y0            <= 16'd0;
            s1_y1            <= 16'd0;
        end else begin
            s1_valid         <= s0_valid;
            s1_endpoint_zero <= s0_endpoint_zero;
            s1_frac          <= s0_frac;
            s1_f_init        <= s0_f_init;
            if (s0_valid) begin
                s1_y0 <= lut_mem[s0_idx];
                if (s0_idx == 8'hFF)
                    s1_y1 <= lut_mem[s0_idx];
                else
                    s1_y1 <= lut_mem[s0_idx + 8'd1];
            end
        end
    end

    // -------------------------------
    // Stage 2: interpolate decay
    // -------------------------------
    wire signed [17:0] s2_diff_w   = $signed({1'b0, s1_y1}) - $signed({1'b0, s1_y0});
    (* use_dsp = "yes" *) wire signed [25:0] s2_prod_w   = s2_diff_w * $signed({1'b0, s1_frac});
    wire signed [17:0] s2_interp_w = (s2_prod_w >= 0)
                                     ? ($signed({1'b0, s1_y0}) + ((s2_prod_w + 26'sd128) >>> 8))
                                     : ($signed({1'b0, s1_y0}) + ((s2_prod_w - 26'sd128) >>> 8));

    reg                 s2_valid;
    reg                 s2_endpoint_zero;
    reg [15:0]          s2_f_init;
    reg [15:0]          s2_decay;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s2_valid         <= 1'b0;
            s2_endpoint_zero <= 1'b0;
            s2_f_init        <= 16'd0;
            s2_decay         <= 16'd0;
        end else begin
            s2_valid         <= s1_valid;
            s2_endpoint_zero <= s1_endpoint_zero;
            s2_f_init        <= s1_f_init;
            if (s1_valid) begin
                if (s1_endpoint_zero)
                    s2_decay <= 16'd0;
                else if (s2_interp_w < 0)
                    s2_decay <= 16'd0;
                else if (s2_interp_w > 18'sd65535)
                    s2_decay <= 16'hFFFF;
                else
                    s2_decay <= s2_interp_w[15:0];
            end
        end
    end

    // -------------------------------
    // Stage 3: multiply f_init * decay
    // -------------------------------
    (* use_dsp = "yes" *) wire [31:0] s3_prod_w = s2_f_init * s2_decay;

    reg                 s3_valid;
    reg                 s3_endpoint_zero;
    reg [31:0]          s3_product;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s3_valid         <= 1'b0;
            s3_endpoint_zero <= 1'b0;
            s3_product       <= 32'd0;
        end else begin
            s3_valid         <= s2_valid;
            s3_endpoint_zero <= s2_endpoint_zero;
            if (s2_valid)
                s3_product <= s3_prod_w;
        end
    end

    // -------------------------------
    // Stage 4: exact divide-by-65535 and output register
    // q = floor((n)/65535) can be computed exactly for our range with:
    // q = (n + 1 + (n >> 16)) >> 16
    // Here n = product + 32767 for round-to-nearest behavior.
    // -------------------------------
    wire [32:0] s4_num_w    = {1'b0, s3_product} + 33'd32767;
    wire [32:0] s4_divsum_w = s4_num_w + 33'd1 + (s4_num_w >> 16);
    wire [16:0] s4_quot_w   = s4_divsum_w[32:16];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_o         <= 1'b0;
            fidelity_q016_o <= 16'd0;
        end else begin
            valid_o <= s3_valid;
            if (s3_valid) begin
                if (s3_endpoint_zero)
                    fidelity_q016_o <= 16'd0;
                else if (s4_quot_w > 17'd65535)
                    fidelity_q016_o <= 16'hFFFF;
                else
                    fidelity_q016_o <= s4_quot_w[15:0];
            end
        end
    end

endmodule
