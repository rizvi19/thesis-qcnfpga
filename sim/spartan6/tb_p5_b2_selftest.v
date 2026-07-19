`timescale 1ns / 1ps

module tb_p5_b2_selftest;
    reg clk;
    reg rst;
    wire heartbeat;
    wire pass_led;
    wire fail_led;
    wire done_led;
    wire [7:0] seg_n;
    wire [3:0] an_n;

    p5_b2_selftest_top #(
        .HEARTBEAT_BIT(3),
        .LUT_FILE("rtl/spartan6/p5_b2_exp_lut.mem")
    ) dut (
        .clk_100mhz(clk), .btn_reset(rst), .led_heartbeat(heartbeat),
        .led_pass(pass_led), .led_fail(fail_led), .led_done(done_led),
        .seg_n(seg_n), .an_n(an_n)
    );

    always #5 clk = ~clk;

    initial begin
        clk = 1'b0;
        rst = 1'b1;
        repeat (2) @(posedge clk);
        rst = 1'b0;
        wait (done_led === 1'b1);
        #1;
        if (pass_led !== 1'b1 || fail_led !== 1'b0 || dut.display_value !== 16'hB210)
            $fatal(1, "P5_B2_BOARD_SELFTEST_SIM=FAIL display=%h pass=%b fail=%b",
                dut.display_value, pass_led, fail_led);
        $display("P5_B2_BOARD_CASES=16_OF_16_EXACT_PASS");
        $display("P5_B2_BOARD_DISPLAY=B210_PASS");
        $display("P5_B2_BOARD_SELFTEST_SIM=PASS");
        $finish;
    end
endmodule
