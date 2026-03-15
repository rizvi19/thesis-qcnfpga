`timescale 1ns/1ps

module tb_fdpe;
    localparam integer CLK_PERIOD_NS = 10;
    localparam integer MAX_VECTORS    = 256;
    localparam integer TOL_LSB        = 2;

    reg         clk;
    reg         rst_n;
    reg         valid_i;
    reg [16:0]  x_q4_13_i;
    reg [15:0]  f_init_q016_i;
    wire        valid_o;
    wire [15:0] fidelity_q016_o;

    reg [56:0] vec_mem [0:MAX_VECTORS-1];
    reg [15:0] exp_queue [0:MAX_VECTORS-1];
    reg [16:0] x_queue   [0:MAX_VECTORS-1];
    reg [15:0] f_queue   [0:MAX_VECTORS-1];
    reg [7:0]  id_queue  [0:MAX_VECTORS-1];

    integer vector_count;
    integer i;
    integer in_count;
    integer out_count;
    integer pass_count;
    integer fail_count;
    integer abs_diff;
    integer max_abs_diff;

    integer log_fd;
    integer summary_fd;
    string vectors_file;
    string log_file;
    string summary_file;

    fdpe #(
        .LUT_FILE("results/phase1/exp_lut.hex")
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .valid_i(valid_i),
        .x_q4_13_i(x_q4_13_i),
        .f_init_q016_i(f_init_q016_i),
        .valid_o(valid_o),
        .fidelity_q016_o(fidelity_q016_o)
    );

    always #(CLK_PERIOD_NS/2) clk = ~clk;

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        valid_i = 1'b0;
        x_q4_13_i = 17'd0;
        f_init_q016_i = 16'd0;
        vector_count = 0;
        in_count = 0;
        out_count = 0;
        pass_count = 0;
        fail_count = 0;
        max_abs_diff = 0;

        vectors_file = "tb/fdpe_vectors.memh";
        log_file     = "results/phase1/fdpe_sim_results.csv";
        summary_file = "results/phase1/fdpe_sim_summary.txt";
        void'($value$plusargs("VECTORS=%s", vectors_file));
        void'($value$plusargs("LOG=%s", log_file));
        void'($value$plusargs("SUMMARY=%s", summary_file));

        $display("[TB_FDPE] vectors=%s", vectors_file);
        $display("[TB_FDPE] log=%s", log_file);
        $display("[TB_FDPE] summary=%s", summary_file);

        $readmemh(vectors_file, vec_mem);
        // Icarus Verilog compatibility: avoid break and count consecutive valid entries.
        vector_count = 0;
        for (i = 0; i < MAX_VECTORS; i = i + 1) begin
            if ((vector_count == i) && (^vec_mem[i] !== 1'bx))
                vector_count = vector_count + 1;
        end

        if (vector_count == 0) begin
            $fatal(1, "[TB_FDPE] No vectors loaded. Generate tb/fdpe_vectors.memh first.");
        end

        log_fd = $fopen(log_file, "w");
        if (log_fd == 0)
            $fatal(1, "[TB_FDPE] Could not open log file: %s", log_file);
        $fwrite(log_fd, "case_id,x_q4_13,f_init_q016,expected_q016,observed_q016,abs_diff_lsb,pass\n");

        repeat (4) @(posedge clk);
        rst_n <= 1'b1;
        @(posedge clk);

        for (i = 0; i < vector_count; i = i + 1) begin
            @(posedge clk);
            valid_i       <= 1'b1;
            x_q4_13_i     <= vec_mem[i][48:32];
            f_init_q016_i <= vec_mem[i][31:16];
            id_queue[in_count]  <= vec_mem[i][56:49];
            x_queue[in_count]   <= vec_mem[i][48:32];
            f_queue[in_count]   <= vec_mem[i][31:16];
            exp_queue[in_count] <= vec_mem[i][15:0];
            in_count = in_count + 1;
        end

        @(posedge clk);
        valid_i <= 1'b0;
        x_q4_13_i <= 17'd0;
        f_init_q016_i <= 16'd0;

        wait (out_count == vector_count);
        repeat (2) @(posedge clk);

        summary_fd = $fopen(summary_file, "w");
        if (summary_fd == 0)
            $fatal(1, "[TB_FDPE] Could not open summary file: %s", summary_file);
        $fwrite(summary_fd, "FDPE simulation summary\n");
        $fwrite(summary_fd, "vector_count=%0d\n", vector_count);
        $fwrite(summary_fd, "pass_count=%0d\n", pass_count);
        $fwrite(summary_fd, "fail_count=%0d\n", fail_count);
        $fwrite(summary_fd, "max_abs_diff_lsb=%0d\n", max_abs_diff);
        $fwrite(summary_fd, "tolerance_lsb=%0d\n", TOL_LSB);
        $fclose(summary_fd);
        $fclose(log_fd);

        if (fail_count == 0)
            $display("[TB_FDPE] PASS: vectors=%0d max_abs_diff_lsb=%0d", vector_count, max_abs_diff);
        else begin
            $display("[TB_FDPE] FAIL: fails=%0d max_abs_diff_lsb=%0d", fail_count, max_abs_diff);
            $fatal(1, "[TB_FDPE] Simulation failed.");
        end

        $finish;
    end

    always @(posedge clk) begin
        if (rst_n && valid_o) begin
            abs_diff = (fidelity_q016_o >= exp_queue[out_count]) ?
                       (fidelity_q016_o - exp_queue[out_count]) :
                       (exp_queue[out_count] - fidelity_q016_o);
            if (abs_diff > max_abs_diff)
                max_abs_diff = abs_diff;

            if (abs_diff <= TOL_LSB) begin
                pass_count = pass_count + 1;
                $fwrite(log_fd, "%0d,%0d,%0d,%0d,%0d,%0d,1\n",
                        id_queue[out_count], x_queue[out_count], f_queue[out_count],
                        exp_queue[out_count], fidelity_q016_o, abs_diff);
            end else begin
                fail_count = fail_count + 1;
                $fwrite(log_fd, "%0d,%0d,%0d,%0d,%0d,%0d,0\n",
                        id_queue[out_count], x_queue[out_count], f_queue[out_count],
                        exp_queue[out_count], fidelity_q016_o, abs_diff);
                $display("[TB_FDPE][MISMATCH] case_id=%0d expected=%0d observed=%0d abs_diff=%0d x_q4_13=%0d f_init=%0d",
                         id_queue[out_count], exp_queue[out_count], fidelity_q016_o, abs_diff,
                         x_queue[out_count], f_queue[out_count]);
            end
            out_count = out_count + 1;
        end
    end

endmodule
