`timescale 1ns / 1ps

module tb_p5_b3_selftest;
    reg clk;
    reg rst;
    wire led_heartbeat;
    wire led_pass;
    wire led_fail;
    wire led_done;
    wire [7:0] seg_n;
    wire [3:0] an_n;
    integer cycles;

    p5_b3_selftest_top #(.HEARTBEAT_BIT(3)) dut (
        .clk_100mhz(clk), .btn_reset(rst),
        .led_heartbeat(led_heartbeat), .led_pass(led_pass),
        .led_fail(led_fail), .led_done(led_done),
        .seg_n(seg_n), .an_n(an_n)
    );

    always #5 clk = ~clk;

    initial begin
        clk = 1'b0;
        rst = 1'b1;
        repeat (3) @(posedge clk);
        rst = 1'b0;
        cycles = 0;
        while (!led_done && cycles < 4000) begin
            @(posedge clk);
            cycles = cycles + 1;
        end
        if (!led_done || !led_pass || led_fail || dut.pass_count != 8'd16 ||
            dut.display_value != 16'hB310) begin
            $display("P5_B3_BOARD_SELFTEST_SIM=FAIL pass=%0d fail=%0d display=%04x",
                     led_pass, led_fail, dut.display_value);
            $fatal(1, "P5_B3_BOARD_SELFTEST_SIM=FAIL");
        end
        rst = 1'b1;
        repeat (2) @(posedge clk);
        rst = 1'b0;
        if (led_done) begin
            $display("P5_B3_BOARD_RESET_SIM=FAIL");
            $fatal(1, "P5_B3_BOARD_RESET_SIM=FAIL");
        end
        $display("P5_B3_BOARD_CASES=16_OF_16_EXACT_PASS");
        $display("P5_B3_BOARD_RESET=PASS");
        $finish;
    end
endmodule
