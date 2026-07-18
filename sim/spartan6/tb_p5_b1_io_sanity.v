`timescale 1ns / 1ps

module tb_p5_b1_io_sanity;

    localparam integer TEST_CLK_HZ    = 1000000;
    localparam integer TEST_UPDATE_HZ = 500;
    localparam integer TEST_BAUD      = 100000;
    localparam integer CLKS_PER_BIT   = 10;

    reg clk_100mhz;
    reg btn_reset;
    wire led_heartbeat;
    wire led_reset;
    wire [7:0] seg_n;
    wire [3:0] an_n;
    wire uart_tx;

    integer errors;
    integer index;
    integer scan_cycle;
    integer seen_an0;
    integer seen_an1;
    integer seen_an2;
    integer seen_an3;
    reg [7:0] received;

    p5_b1_top #(
        .CLK_HZ(TEST_CLK_HZ),
        .UPDATE_HZ(TEST_UPDATE_HZ),
        .UART_BAUD(TEST_BAUD),
        .SCAN_COUNTER_BITS(4)
    ) dut (
        .clk_100mhz(clk_100mhz),
        .btn_reset(btn_reset),
        .led_heartbeat(led_heartbeat),
        .led_reset(led_reset),
        .seg_n(seg_n),
        .an_n(an_n),
        .uart_tx(uart_tx)
    );

    always #5 clk_100mhz = ~clk_100mhz;

    function [7:0] expected_byte;
        input integer byte_index;
        begin
            case (byte_index)
                0:  expected_byte = "Q";
                1:  expected_byte = "F";
                2:  expected_byte = "5";
                3:  expected_byte = "B";
                4:  expected_byte = "1";
                5:  expected_byte = ",";
                6:  expected_byte = "1";
                7:  expected_byte = ",";
                8:  expected_byte = "0";
                9:  expected_byte = "0";
                10: expected_byte = "0";
                11: expected_byte = "1";
                12: expected_byte = ",";
                13: expected_byte = "0";
                14: expected_byte = 8'h0d;
                15: expected_byte = 8'h0a;
                default: expected_byte = 8'h3f;
            endcase
        end
    endfunction

    task check;
        input condition;
        input [8*80-1:0] message;
        begin
            if (!condition) begin
                errors = errors + 1;
                $display("CHECK_FAIL=%0s", message);
            end
        end
    endtask

    task receive_uart_byte;
        output [7:0] value;
        integer bit_number;
        begin
            @(negedge uart_tx);
            repeat (CLKS_PER_BIT + (CLKS_PER_BIT / 2)) @(posedge clk_100mhz);
            for (bit_number = 0; bit_number < 8; bit_number = bit_number + 1) begin
                value[bit_number] = uart_tx;
                repeat (CLKS_PER_BIT) @(posedge clk_100mhz);
            end
            check(uart_tx === 1'b1, "UART stop bit must be high");
        end
    endtask

    initial begin
        clk_100mhz = 1'b0;
        btn_reset  = 1'b1;
        errors     = 0;
        seen_an0   = 0;
        seen_an1   = 0;
        seen_an2   = 0;
        seen_an3   = 0;

        repeat (6) @(posedge clk_100mhz);
        #1;
        check(led_reset === 1'b1, "synchronized reset LED must assert");
        check(dut.counter_value === 16'h0000, "reset must clear displayed counter");
        check(uart_tx === 1'b1, "UART must idle high during reset");

        btn_reset = 1'b0;
        repeat (4) @(posedge clk_100mhz);
        #1;
        check(led_reset === 1'b0, "synchronized reset LED must deassert");
        check(dut.counter_value === 16'h0000, "counter must remain zero after reset release");

        for (index = 0; index < 16; index = index + 1) begin
            receive_uart_byte(received);
            if (received !== expected_byte(index)) begin
                errors = errors + 1;
                $display("UART_BYTE_FAIL index=%0d expected=%02x actual=%02x",
                         index, expected_byte(index), received);
            end
        end

        check(dut.counter_value === 16'h0001, "first record must snapshot displayed counter 0001");
        check(led_heartbeat === 1'b1, "heartbeat must reflect counter bit zero");

        for (scan_cycle = 0; scan_cycle < 64; scan_cycle = scan_cycle + 1) begin
            @(posedge clk_100mhz);
            #1;
            case (an_n)
                4'b1110: begin
                    seen_an0 = 1;
                    check(seg_n === 8'b11111001, "AN0 must display hexadecimal 1");
                end
                4'b1101: begin
                    seen_an1 = 1;
                    check(seg_n === 8'b11000000, "AN1 must display hexadecimal 0");
                end
                4'b1011: begin
                    seen_an2 = 1;
                    check(seg_n === 8'b11000000, "AN2 must display hexadecimal 0");
                end
                4'b0111: begin
                    seen_an3 = 1;
                    check(seg_n === 8'b11000000, "AN3 must display hexadecimal 0");
                end
                default: check(1'b0, "exactly one display anode must be active");
            endcase
        end

        check(seen_an0 && seen_an1 && seen_an2 && seen_an3,
              "all four display digits must scan");

        btn_reset = 1'b1;
        repeat (4) @(posedge clk_100mhz);
        #1;
        check(led_reset === 1'b1, "second reset must visibly assert");
        check(dut.counter_value === 16'h0000, "second reset must return counter to 0000");
        check(uart_tx === 1'b1, "second reset must return UART to idle");

        if (errors == 0) begin
            $display("P5_B1_SIM_UART_BYTES=16_OF_16_PASS");
            $display("P5_B1_SIM_DISPLAY_DIGITS=4_OF_4_PASS");
            $display("P5_B1_SIM_RESET_CASES=2_OF_2_PASS");
            $display("P5_B1_SIM=PASS");
            $finish;
        end else begin
            $display("P5_B1_SIM=FAIL errors=%0d", errors);
            $finish(1);
        end
    end

endmodule
