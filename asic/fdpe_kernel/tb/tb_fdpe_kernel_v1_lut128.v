// ============================================================================
// Testbench for QFlow FDPE Kernel V1 — 128-entry LUT
// ============================================================================

`timescale 1ns/1ps

module tb_fdpe_kernel_v1_lut128;

    reg clk;
    reg rst_n;
    reg start;
    reg [15:0] f_init_q016;
    reg [6:0]  lut_index;

    wire done;
    wire [15:0] fidelity_q016;

    fdpe_kernel_v1_lut128 dut (
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
        input [6:0]  t_idx;
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
        $dumpfile("asic/fdpe_kernel/results/fdpe_kernel_v1_lut128.vcd");
        $dumpvars(0, tb_fdpe_kernel_v1_lut128);

        rst_n = 1'b0;
        start = 1'b0;
        f_init_q016 = 16'd0;
        lut_index = 7'd0;

        repeat (5) @(posedge clk);
        rst_n = 1'b1;

        // Equivalent x-positions to V0 cases:
        // V0 index 0   -> V1 index 0
        // V0 index 8   -> V1 index 4
        // V0 index 32  -> V1 index 16
        // V0 index 64  -> V1 index 32
        // V0 index 128 -> V1 index 64
        // V0 index 240 -> V1 index 120

        run_case(16'd65535, 7'd0);
        run_case(16'd62259, 7'd4);
        run_case(16'd58982, 7'd16);
        run_case(16'd49152, 7'd32);
        run_case(16'd32768, 7'd64);
        run_case(16'd65535, 7'd120);

        repeat (5) @(posedge clk);

        $display("FDPE_KERNEL_V1_LUT128_SIM_PASS");
        $finish;
    end

endmodule
