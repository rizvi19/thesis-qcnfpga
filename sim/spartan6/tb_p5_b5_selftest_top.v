`timescale 1ns / 1ps

module tb_p5_b5_selftest_top;

    reg clk;
    reg rst;

    wire led_heartbeat;
    wire led_pass;
    wire led_fail;
    wire led_done;
    wire [7:0] seg_n;
    wire [3:0] an_n;

    p5_b5_selftest_top uut (
        .clk_100mhz(clk),
        .btn_reset(rst),
        .led_heartbeat(led_heartbeat),
        .led_pass(led_pass),
        .led_fail(led_fail),
        .led_done(led_done),
        .seg_n(seg_n),
        .an_n(an_n)
    );

    initial begin
        clk = 1'b0;
        rst = 1'b1;
        #37;
        rst = 1'b0;
    end

    always #5 clk = ~clk;

    initial begin
        wait (led_done == 1'b1);
        #30;

        $display("FINAL_TEST_ID=%0d", uut.test_id);
        $display("FINAL_PASS=%0d", led_pass);
        $display("FINAL_FAIL=%0d", led_fail);
        $display("FINAL_DONE=%0d", led_done);

        if ((uut.test_id == 5'd16) &&
            (led_pass == 1'b1) &&
            (led_fail == 1'b0) &&
            (led_done == 1'b1))
            $display("P5_B5_BOARD_SELFTEST_SIMULATION=17_OF_17_PASS");
        else
            $display("P5_B5_BOARD_SELFTEST_SIMULATION=FAIL");

        $finish;
    end

    initial begin
        #5000000;
        $display("P5_B5_BOARD_SELFTEST_SIMULATION=FAIL_TIMEOUT");
        $display("TEST_ID_AT_TIMEOUT=%0d", uut.test_id);
        $finish;
    end

endmodule
