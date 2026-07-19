`timescale 1ns / 1ps

module p5_b3_iterative_divider (
    input  wire        clk,
    input  wire        rst,
    input  wire        start,
    input  wire [47:0] dividend,
    input  wire [17:0] divisor,
    output wire        ready,
    output reg         busy,
    output reg         done,
    output reg  [47:0] quotient
);

    reg [47:0] dividend_shift;
    reg [47:0] quotient_work;
    reg [18:0] remainder;
    reg [17:0] divisor_reg;
    reg [5:0] count;
    reg [18:0] trial_remainder;
    reg [47:0] quotient_next;

    assign ready = ~busy;

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;
            done <= 1'b0;
            quotient <= 48'd0;
            dividend_shift <= 48'd0;
            quotient_work <= 48'd0;
            remainder <= 19'd0;
            divisor_reg <= 18'd0;
            count <= 6'd0;
        end else begin
            done <= 1'b0;
            if (!busy) begin
                if (start) begin
                    dividend_shift <= dividend;
                    quotient_work <= 48'd0;
                    remainder <= 19'd0;
                    divisor_reg <= divisor;
                    count <= 6'd0;
                    busy <= 1'b1;
                end
            end else begin
                trial_remainder = {remainder[17:0], dividend_shift[47]};
                dividend_shift <= {dividend_shift[46:0], 1'b0};
                if (trial_remainder >= {1'b0, divisor_reg}) begin
                    remainder <= trial_remainder - {1'b0, divisor_reg};
                    quotient_next = {quotient_work[46:0], 1'b1};
                end else begin
                    remainder <= trial_remainder;
                    quotient_next = {quotient_work[46:0], 1'b0};
                end
                quotient_work <= quotient_next;
                if (count == 6'd47) begin
                    quotient <= quotient_next;
                    busy <= 1'b0;
                    done <= 1'b1;
                end else begin
                    count <= count + 1'b1;
                end
            end
        end
    end

endmodule
