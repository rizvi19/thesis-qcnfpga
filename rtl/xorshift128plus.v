`timescale 1ns/1ps

module xorshift128plus (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        seed_valid_i,
    input  wire [63:0] seed0_i,
    input  wire [63:0] seed1_i,
    input  wire        enable_i,
    output reg  [63:0] rand_o,
    output reg         valid_o,
    output reg         seeded_o
);
    reg [63:0] s0_reg;
    reg [63:0] s1_reg;
    reg [63:0] x;
    reg [63:0] y;
    reg [63:0] s1_shifted;
    reg [63:0] s0_next;
    reg [63:0] s1_next;
    reg [63:0] sum_next;

    always @(*) begin
        x = s0_reg;
        y = s1_reg;
        s0_next    = y;
        s1_shifted = x ^ (x << 23);
        s1_shifted = s1_shifted ^ (s1_shifted >> 17);
        s1_shifted = s1_shifted ^ y;
        s1_shifted = s1_shifted ^ (y >> 26);
        s1_next    = s1_shifted;
        sum_next   = s1_next + s0_next;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s0_reg   <= 64'd1;
            s1_reg   <= 64'd2;
            rand_o   <= 64'd0;
            valid_o  <= 1'b0;
            seeded_o <= 1'b0;
        end else begin
            valid_o <= 1'b0;
            if (seed_valid_i) begin
                if (seed0_i == 64'd0 && seed1_i == 64'd0) begin
                    s0_reg <= 64'd1;
                    s1_reg <= 64'd2;
                end else begin
                    s0_reg <= seed0_i;
                    s1_reg <= seed1_i;
                end
                rand_o   <= 64'd0;
                valid_o  <= 1'b0;
                seeded_o <= 1'b1;
            end else if (enable_i && seeded_o) begin
                s0_reg  <= s0_next;
                s1_reg  <= s1_next;
                rand_o  <= sum_next;
                valid_o <= 1'b1;
            end
        end
    end
endmodule
