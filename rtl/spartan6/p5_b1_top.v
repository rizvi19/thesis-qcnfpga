`timescale 1ns / 1ps

module p5_b1_top #(
    parameter integer CLK_HZ            = 100000000,
    parameter integer UPDATE_HZ         = 1,
    parameter integer UART_BAUD         = 115200,
    parameter integer SCAN_COUNTER_BITS = 18
) (
    input  wire       clk_100mhz,
    input  wire       btn_reset,
    output wire       led_heartbeat,
    output wire       led_reset,
    output wire [7:0] seg_n,
    output wire [3:0] an_n,
    output wire       uart_tx
);

    localparam integer UPDATE_TICKS = CLK_HZ / UPDATE_HZ;

    reg reset_meta;
    reg reset_sync;
    reg [31:0] update_divider;
    reg [15:0] counter_value;
    reg [15:0] record_value;
    reg        record_active;
    reg [4:0]  record_index;

    wire       uart_ready;
    wire       uart_busy;
    wire       uart_valid;
    wire       uart_accept;
    wire [7:0] uart_data;

    assign led_heartbeat = counter_value[0];
    assign led_reset     = reset_sync;
    assign uart_valid    = record_active;
    assign uart_accept   = uart_valid & uart_ready;
    assign uart_data     = record_byte(record_index, record_value);

    function [7:0] hex_ascii;
        input [3:0] nibble;
        begin
            if (nibble < 10)
                hex_ascii = 8'h30 + nibble;
            else
                hex_ascii = 8'h41 + (nibble - 10);
        end
    endfunction

    function [7:0] record_byte;
        input [4:0]  index;
        input [15:0] value;
        begin
            case (index)
                5'd0:  record_byte = "Q";
                5'd1:  record_byte = "F";
                5'd2:  record_byte = "5";
                5'd3:  record_byte = "B";
                5'd4:  record_byte = "1";
                5'd5:  record_byte = ",";
                5'd6:  record_byte = "1";
                5'd7:  record_byte = ",";
                5'd8:  record_byte = hex_ascii(value[15:12]);
                5'd9:  record_byte = hex_ascii(value[11:8]);
                5'd10: record_byte = hex_ascii(value[7:4]);
                5'd11: record_byte = hex_ascii(value[3:0]);
                5'd12: record_byte = ",";
                5'd13: record_byte = "0";
                5'd14: record_byte = 8'h0d;
                5'd15: record_byte = 8'h0a;
                default: record_byte = 8'h3f;
            endcase
        end
    endfunction

    always @(posedge clk_100mhz) begin
        reset_meta <= btn_reset;
        reset_sync <= reset_meta;
    end

    always @(posedge clk_100mhz) begin
        if (reset_sync) begin
            update_divider <= 32'd0;
            counter_value  <= 16'd0;
            record_value   <= 16'd0;
            record_active  <= 1'b0;
            record_index   <= 5'd0;
        end else begin
            if (update_divider == UPDATE_TICKS - 1) begin
                update_divider <= 32'd0;
                if (!record_active) begin
                    counter_value <= counter_value + 1'b1;
                    record_value  <= counter_value + 1'b1;
                    record_active <= 1'b1;
                    record_index  <= 5'd0;
                end
            end else begin
                update_divider <= update_divider + 1'b1;
            end

            if (uart_accept) begin
                if (record_index == 5'd15) begin
                    record_active <= 1'b0;
                    record_index  <= 5'd0;
                end else begin
                    record_index <= record_index + 1'b1;
                end
            end
        end
    end

    p5_b1_sevenseg #(
        .SCAN_COUNTER_BITS(SCAN_COUNTER_BITS)
    ) display_i (
        .clk(clk_100mhz),
        .rst(reset_sync),
        .value(counter_value),
        .seg_n(seg_n),
        .an_n(an_n)
    );

    p5_b1_uart_tx #(
        .CLK_HZ(CLK_HZ),
        .BAUD(UART_BAUD)
    ) uart_i (
        .clk(clk_100mhz),
        .rst(reset_sync),
        .data_valid(uart_valid),
        .data_byte(uart_data),
        .ready(uart_ready),
        .tx(uart_tx),
        .busy(uart_busy)
    );

endmodule
