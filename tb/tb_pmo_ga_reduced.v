
`timescale 1ns/1ps
module tb_pmo_ga_reduced;
    localparam integer MAX_VECTORS = 64;

    reg clk, rst_n, start, cand_valid, batch_done, rand_tiebreak;
    reg [15:0] cand_id;
    reg [31:0] cand_latency;
    reg [15:0] cand_fidelity, cand_util;

    wire result_valid;
    wire [15:0] result_id;
    wire [31:0] result_latency;
    wire [15:0] result_fidelity, result_util;

    reg [79:0] vec_mem [0:MAX_VECTORS-1];
    integer vector_count, i, log_fd, err_count;
    integer expected_best_id, expected_latency, expected_fidelity, expected_util;

    reg [1023:0] vectors_file;
    reg [1023:0] log_file;
    reg [1023:0] summary_file;

    pmo_ga_reduced dut (
        .clk(clk), .rst_n(rst_n), .start_i(start),
        .cand_valid_i(cand_valid), .cand_id_i(cand_id),
        .cand_latency_i(cand_latency), .cand_fidelity_i(cand_fidelity),
        .cand_util_i(cand_util), .batch_done_i(batch_done),
        .rand_tiebreak_i(rand_tiebreak),
        .result_valid_o(result_valid), .result_id_o(result_id),
        .result_latency_o(result_latency), .result_fidelity_o(result_fidelity),
        .result_util_o(result_util)
    );

    always #5 clk = ~clk;

    initial begin
        clk=0; rst_n=0; start=0; cand_valid=0; batch_done=0; rand_tiebreak=0;
        cand_id=0; cand_latency=0; cand_fidelity=0; cand_util=0; err_count=0;

        if (!$value$plusargs("VECTORS=%s", vectors_file)) vectors_file = "tb/pmo_ga_reduced_candidates.memh";
        if (!$value$plusargs("LOG=%s", log_file))         log_file     = "results/phase4/pmo_ga_reduced_sim_results.csv";
        if (!$value$plusargs("SUMMARY=%s", summary_file)) summary_file = "results/phase4/pmo_ga_reduced_sim_summary.txt";

        $display("[TB_PMO_GA_REDUCED] vectors=%0s", vectors_file);
        $display("[TB_PMO_GA_REDUCED] log=%0s", log_file);
        $display("[TB_PMO_GA_REDUCED] summary=%0s", summary_file);

        $readmemh(vectors_file, vec_mem);
        vector_count = 0;
        for (i=0; i<MAX_VECTORS; i=i+1) begin
            if ((vector_count == i) && (^vec_mem[i] !== 1'bx))
                vector_count = vector_count + 1;
        end

        log_fd = $fopen(log_file, "w");
        $fwrite(log_fd, "idx,path_id,latency_q16_16,fidelity_q0_16,util_q0_16\n");

        repeat (3) @(posedge clk);
        rst_n <= 1'b1;
        @(posedge clk);
        start <= 1'b1;
        @(posedge clk);
        start <= 1'b0;

        for (i=0; i<vector_count; i=i+1) begin
            @(posedge clk);
            cand_valid    <= 1'b1;
            cand_id       <= vec_mem[i][79:64];
            cand_latency  <= vec_mem[i][63:32];
            cand_fidelity <= vec_mem[i][31:16];
            cand_util     <= vec_mem[i][15:0];
            rand_tiebreak <= i[0];
            $fwrite(log_fd, "%0d,%0d,%0d,%0d,%0d\n", i, vec_mem[i][79:64], vec_mem[i][63:32], vec_mem[i][31:16], vec_mem[i][15:0]);
        end

        @(posedge clk);
        cand_valid <= 1'b0;
        cand_id <= 0; cand_latency <= 0; cand_fidelity <= 0; cand_util <= 0;
        batch_done <= 1'b1;
        @(posedge clk);
        batch_done <= 1'b0;

        wait (result_valid === 1'b1);
        @(posedge clk);

        expected_best_id  = 4;
        expected_latency  = 32'h00050000;
        expected_fidelity = 16'd60948;
        expected_util     = 16'd14418;

        if (result_id !== expected_best_id[15:0]) begin
            err_count = err_count + 1;
            $display("[TB_PMO_GA_REDUCED][MISMATCH] expected_id=%0d observed_id=%0d", expected_best_id, result_id);
        end
        if (result_latency !== expected_latency[31:0]) begin
            err_count = err_count + 1;
            $display("[TB_PMO_GA_REDUCED][MISMATCH] expected_latency=%0d observed_latency=%0d", expected_latency, result_latency);
        end
        if (result_fidelity !== expected_fidelity[15:0]) begin
            err_count = err_count + 1;
            $display("[TB_PMO_GA_REDUCED][MISMATCH] expected_fidelity=%0d observed_fidelity=%0d", expected_fidelity, result_fidelity);
        end
        if (result_util !== expected_util[15:0]) begin
            err_count = err_count + 1;
            $display("[TB_PMO_GA_REDUCED][MISMATCH] expected_util=%0d observed_util=%0d", expected_util, result_util);
        end

        begin : summary_block
            integer sf;
            sf = $fopen(summary_file, "w");
            $fwrite(sf, "PMO-GA reduced kernel summary\n");
            $fwrite(sf, "vector_count=%0d\n", vector_count);
            $fwrite(sf, "expected_best_id=%0d\n", expected_best_id);
            $fwrite(sf, "observed_best_id=%0d\n", result_id);
            $fwrite(sf, "observed_latency=%0d\n", result_latency);
            $fwrite(sf, "observed_fidelity=%0d\n", result_fidelity);
            $fwrite(sf, "observed_util=%0d\n", result_util);
            $fwrite(sf, "fail_count=%0d\n", err_count);
            $fclose(sf);
        end

        $fclose(log_fd);
        if (err_count == 0) begin
            $display("[TB_PMO_GA_REDUCED] PASS: vectors=%0d best_id=%0d", vector_count, result_id);
        end else begin
            $display("[TB_PMO_GA_REDUCED] FAIL: err_count=%0d", err_count);
            $fatal(1, "[TB_PMO_GA_REDUCED] Simulation failed.");
        end
        $finish;
    end
endmodule
