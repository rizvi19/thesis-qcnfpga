`timescale 1ns / 1ps

module p5_b1_uart_tx #(
    parameter integer CLK_HZ = 100000000,
    parameter integer BAUD   = 115200
) (
    input  wire       clk,
    input  wire       rst,
    input  wire       data_valid,
    input  wire [7:0] data_byte,
    output wire       ready,
    output reg        tx,
    output reg        busy
);

    localparam integer CLKS_PER_BIT = (CLK_HZ + (BAUD / 2)) / BAUD;

    reg [31:0] baud_counter;
    reg [3:0]  bit_index;
    reg [9:0]  frame;

    assign ready = ~busy;

    always @(posedge clk) begin
        if (rst) begin
            baud_counter <= 32'd0;
            bit_index    <= 4'd0;
            frame        <= 10'h3ff;
            tx           <= 1'b1;
            busy         <= 1'b0;
        end else if (!busy) begin
            baud_counter <= 32'd0;
            bit_index    <= 4'd0;
            tx           <= 1'b1;
            if (data_valid) begin
                frame <= {1'b1, data_byte, 1'b0};
                tx    <= 1'b0;
                busy  <= 1'b1;
            end
        end else if (baud_counter == CLKS_PER_BIT - 1) begin
            baud_counter <= 32'd0;
            if (bit_index == 4'd9) begin
                bit_index <= 4'd0;
                tx        <= 1'b1;
                busy      <= 1'b0;
            end else begin
                bit_index <= bit_index + 1'b1;
                tx        <= frame[bit_index + 1'b1];
            end
        end else begin
            baud_counter <= baud_counter + 1'b1;
        end
    end

endmodule
