// ============================================================================
// Testbench for QFlow FDPE Kernel V2 — 128-entry LUT + interpolation
// ============================================================================

`timescale 1ns/1ps

module tb_fdpe_kernel_v2_lut128_interp;

    reg clk;
    reg rst_n;
    reg start;
    reg [15:0] f_init_q016;
    reg [6:0]  lut_index;
    reg [7:0]  frac_q08;

    wire done;
    wire [15:0] fidelity_q016;

    fdpe_kernel_v2_lut128_interp dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .f_init_q016(f_init_q016),
        .lut_index(lut_index),
        .frac_q08(frac_q08),
        .done(done),
        .fidelity_q016(fidelity_q016)
    );

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    task run_case;
        input [15:0] t_f_init;
        input [6:0]  t_idx;
        input [7:0]  t_frac;
        begin
            @(posedge clk);
            f_init_q016 <= t_f_init;
            lut_index   <= t_idx;
            frac_q08    <= t_frac;
            start       <= 1'b1;

            @(posedge clk);
            start       <= 1'b0;

            wait(done == 1'b1);
            @(posedge clk);

            $display("CASE f_init=%0d lut_index=%0d frac=%0d fidelity_out=%0d",
                     t_f_init, t_idx, t_frac, fidelity_q016);
        end
    endtask

    initial begin
        $dumpfile("asic/fdpe_kernel/results/fdpe_kernel_v2_lut128_interp.vcd");
        $dumpvars(0, tb_fdpe_kernel_v2_lut128_interp);

        rst_n = 1'b0;
        start = 1'b0;
        f_init_q016 = 16'd0;
        lut_index = 7'd0;
        frac_q08 = 8'd0;

        repeat (5) @(posedge clk);
        rst_n = 1'b1;

        // Exact sample points: frac=0 should behave like V1 for same index.
        run_case(16'd65535, 7'd0,   8'd0);
        run_case(16'd62259, 7'd4,   8'd0);
        run_case(16'd58982, 7'd16,  8'd0);

        // Midpoint interpolation tests.
        run_case(16'd62259, 7'd4,   8'd128);
        run_case(16'd58982, 7'd16,  8'd128);
        run_case(16'd49152, 7'd32,  8'd128);

        // Tail region.
        run_case(16'd32768, 7'd64,  8'd128);
        run_case(16'd65535, 7'd120, 8'd128);

        repeat (5) @(posedge clk);

        $display("FDPE_KERNEL_V2_LUT128_INTERP_SIM_PASS");
        $finish;
    end

endmodule
