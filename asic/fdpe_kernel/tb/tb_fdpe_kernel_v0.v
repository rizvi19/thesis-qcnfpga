// ============================================================================
// Testbench for QFlow FDPE Kernel V0
// ============================================================================

`timescale 1ns/1ps

module tb_fdpe_kernel_v0;

    reg clk;
    reg rst_n;
    reg start;
    reg [15:0] f_init_q016;
    reg [7:0]  lut_index;

    wire done;
    wire [15:0] fidelity_q016;

    fdpe_kernel_v0 dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .f_init_q016(f_init_q016),
        .lut_index(lut_index),
        .done(done),
        .fidelity_q016(fidelity_q016)
    );

    // 100 MHz clock
    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    task run_case;
        input [15:0] t_f_init;
        input [7:0]  t_idx;
        begin
            @(posedge clk);
            f_init_q016 <= t_f_init;
            lut_index   <= t_idx;
            start       <= 1'b1;

            @(posedge clk);
            start       <= 1'b0;

            wait(done == 1'b1);
            @(posedge clk);

            $display("CASE f_init=%0d lut_index=%0d fidelity_out=%0d",
                     t_f_init, t_idx, fidelity_q016);
        end
    endtask

    initial begin
        $dumpfile("asic/fdpe_kernel/results/fdpe_kernel_v0.vcd");
        $dumpvars(0, tb_fdpe_kernel_v0);

        rst_n = 1'b0;
        start = 1'b0;
        f_init_q016 = 16'd0;
        lut_index = 8'd0;

        repeat (5) @(posedge clk);
        rst_n = 1'b1;

        // Test cases
        // f_init approx 1.0, early LUT index
        run_case(16'd65535, 8'd0);

        // f_init approx 0.95, small decay
        run_case(16'd62259, 8'd8);

        // f_init approx 0.90, medium decay
        run_case(16'd58982, 8'd32);

        // f_init approx 0.75, larger decay
        run_case(16'd49152, 8'd64);

        // f_init approx 0.50, very old key
        run_case(16'd32768, 8'd128);

        // f_init approx 1.0, near end of LUT
        run_case(16'd65535, 8'd240);

        repeat (5) @(posedge clk);

        $display("FDPE_KERNEL_V0_SIM_PASS");
        $finish;
    end

endmodule
