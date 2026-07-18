`timescale 1ns / 1ps

module p5_b1_sevenseg #(
    parameter integer SCAN_COUNTER_BITS = 18
) (
    input  wire        clk,
    input  wire        rst,
    input  wire [15:0] value,
    output reg  [7:0]  seg_n,
    output reg  [3:0]  an_n
);

    reg [SCAN_COUNTER_BITS-1:0] scan_counter;
    reg [3:0] nibble;
    wire [1:0] digit_select;

    assign digit_select = scan_counter[SCAN_COUNTER_BITS-1:SCAN_COUNTER_BITS-2];

    function [6:0] hex_segments_n;
        input [3:0] hex_value;
        begin
            case (hex_value)
                4'h0: hex_segments_n = 7'b1000000;
                4'h1: hex_segments_n = 7'b1111001;
                4'h2: hex_segments_n = 7'b0100100;
                4'h3: hex_segments_n = 7'b0110000;
                4'h4: hex_segments_n = 7'b0011001;
                4'h5: hex_segments_n = 7'b0010010;
                4'h6: hex_segments_n = 7'b0000010;
                4'h7: hex_segments_n = 7'b1111000;
                4'h8: hex_segments_n = 7'b0000000;
                4'h9: hex_segments_n = 7'b0010000;
                4'hA: hex_segments_n = 7'b0001000;
                4'hB: hex_segments_n = 7'b0000011;
                4'hC: hex_segments_n = 7'b1000110;
                4'hD: hex_segments_n = 7'b0100001;
                4'hE: hex_segments_n = 7'b0000110;
                4'hF: hex_segments_n = 7'b0001110;
                default: hex_segments_n = 7'b1111111;
            endcase
        end
    endfunction

    always @(posedge clk) begin
        if (rst)
            scan_counter <= {SCAN_COUNTER_BITS{1'b0}};
        else
            scan_counter <= scan_counter + 1'b1;
    end

    always @* begin
        an_n = 4'b1111;
        case (digit_select)
            2'd0: begin an_n = 4'b1110; nibble = value[3:0];   end
            2'd1: begin an_n = 4'b1101; nibble = value[7:4];   end
            2'd2: begin an_n = 4'b1011; nibble = value[11:8];  end
            default: begin an_n = 4'b0111; nibble = value[15:12]; end
        endcase
        seg_n = {1'b1, hex_segments_n(nibble)};
    end

endmodule
