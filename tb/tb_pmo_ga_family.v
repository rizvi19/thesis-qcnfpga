`timescale 1ns/1ps
module tb_pmo_ga_family;
    localparam integer MAX_VECTORS = 16;
    localparam integer INDEX_W = 6;

    reg clk, rst_n, start, batch_done, rand_tiebreak;
    reg cand_valid;
    reg [15:0] cand_id, cand_fidelity, cand_util, cand_gene;
    reg [31:0] cand_latency;
    wire req_valid, issue_done, result_valid;
    wire [INDEX_W-1:0] req_index;
    wire [15:0] result_id, result_fidelity, result_util, child_gene, mutated_gene;
    wire [31:0] result_latency;

    reg [95:0] vec_mem [0:MAX_VECTORS-1];
    integer vector_count, i, log_fd, err_count;
    integer req_seen_count;
    reg pending_done;

    integer expected_best_id;
    integer expected_latency;
    integer expected_fidelity;
    integer expected_util;
    integer expected_child_gene;
    integer expected_mutated_gene;

    reg [1023:0] vectors_file;
    reg [1023:0] log_file;
    reg [1023:0] summary_file;

    pmo_ga_family #(.INDEX_W(INDEX_W)) dut (
        .clk(clk), .rst_n(rst_n), .start_i(start), .pop_size_i(vector_count[INDEX_W-1:0]),
        .batch_done_i(batch_done), .cand_valid_i(cand_valid), .cand_id_i(cand_id),
        .cand_latency_i(cand_latency), .cand_fidelity_i(cand_fidelity), .cand_util_i(cand_util),
        .cand_gene_i(cand_gene), .rand_tiebreak_i(rand_tiebreak), .req_valid_o(req_valid),
        .req_index_o(req_index), .issue_done_o(issue_done), .result_valid_o(result_valid),
        .result_id_o(result_id), .result_latency_o(result_latency), .result_fidelity_o(result_fidelity),
        .result_util_o(result_util), .child_gene_o(child_gene), .mutated_gene_o(mutated_gene)
    );

    always #5 clk = ~clk;

    initial begin
        clk=0; rst_n=0; start=0; batch_done=0; rand_tiebreak=0;
        cand_valid=0; cand_id=0; cand_latency=0; cand_fidelity=0; cand_util=0; cand_gene=0;
        err_count=0; req_seen_count=0; pending_done=0;

        if (!$value$plusargs("VECTORS=%s", vectors_file)) vectors_file = "tb/pmo_ga_family_vectors.memh";
        if (!$value$plusargs("LOG=%s", log_file))         log_file     = "results/phase5/pmo_ga_family_sim_results.csv";
        if (!$value$plusargs("SUMMARY=%s", summary_file)) summary_file = "results/phase5/pmo_ga_family_sim_summary.txt";

        $display("[TB_PMO_GA_FAMILY] vectors=%0s", vectors_file);
        $display("[TB_PMO_GA_FAMILY] log=%0s", log_file);
        $display("[TB_PMO_GA_FAMILY] summary=%0s", summary_file);

        $readmemh(vectors_file, vec_mem);
        vector_count = 0;
        for (i=0; i<MAX_VECTORS; i=i+1) begin
            if ((vector_count == i) && (^vec_mem[i] !== 1'bx))
                vector_count = vector_count + 1;
        end

        expected_best_id      = 4;
        expected_latency      = 32'h00050000;
        expected_fidelity     = 16'd60948;
        expected_util         = 16'd14418;
        expected_child_gene   = 16'h1278;
        expected_mutated_gene = 16'h127C;

        log_fd = $fopen(log_file, "w");
        $fwrite(log_fd, "kind,idx,id,latency_q16_16,fidelity_q0_16,util_q0_16,child_gene16,mutated_gene16\n");

        repeat (3) @(posedge clk);
        rst_n <= 1'b1;
        @(posedge clk);
        start <= 1'b1;
        @(posedge clk);
        start <= 1'b0;

        wait (result_valid === 1'b1);
        @(posedge clk);

        if (result_id !== expected_best_id[15:0]) begin
            err_count = err_count + 1;
            $display("[TB_PMO_GA_FAMILY][MISMATCH] expected_id=%0d observed_id=%0d", expected_best_id, result_id);
        end
        if (result_latency !== expected_latency[31:0]) begin
            err_count = err_count + 1;
            $display("[TB_PMO_GA_FAMILY][MISMATCH] expected_latency=%0d observed_latency=%0d", expected_latency, result_latency);
        end
        if (result_fidelity !== expected_fidelity[15:0]) begin
            err_count = err_count + 1;
            $display("[TB_PMO_GA_FAMILY][MISMATCH] expected_fidelity=%0d observed_fidelity=%0d", expected_fidelity, result_fidelity);
        end
        if (result_util !== expected_util[15:0]) begin
            err_count = err_count + 1;
            $display("[TB_PMO_GA_FAMILY][MISMATCH] expected_util=%0d observed_util=%0d", expected_util, result_util);
        end
        if (child_gene !== expected_child_gene[15:0]) begin
            err_count = err_count + 1;
            $display("[TB_PMO_GA_FAMILY][MISMATCH] expected_child_gene=%0d observed_child_gene=%0d", expected_child_gene, child_gene);
        end
        if (mutated_gene !== expected_mutated_gene[15:0]) begin
            err_count = err_count + 1;
            $display("[TB_PMO_GA_FAMILY][MISMATCH] expected_mutated_gene=%0d observed_mutated_gene=%0d", expected_mutated_gene, mutated_gene);
        end

        $fwrite(log_fd, "RESULT,0,%0d,%0d,%0d,%0d,%0d,%0d\n", result_id, result_latency, result_fidelity, result_util, child_gene, mutated_gene);

        begin : summary_block
            integer sf;
            sf = $fopen(summary_file, "w");
            $fwrite(sf, "PMO-GA family smoke summary\n");
            $fwrite(sf, "vector_count=%0d\n", vector_count);
            $fwrite(sf, "expected_best_id=%0d\n", expected_best_id);
            $fwrite(sf, "observed_best_id=%0d\n", result_id);
            $fwrite(sf, "observed_latency=%0d\n", result_latency);
            $fwrite(sf, "observed_fidelity=%0d\n", result_fidelity);
            $fwrite(sf, "observed_util=%0d\n", result_util);
            $fwrite(sf, "observed_child_gene=%0d\n", child_gene);
            $fwrite(sf, "observed_mutated_gene=%0d\n", mutated_gene);
            $fwrite(sf, "fail_count=%0d\n", err_count);
            $fclose(sf);
        end

        $fclose(log_fd);
        if (err_count == 0) begin
            $display("[TB_PMO_GA_FAMILY] PASS: vectors=%0d best_id=%0d child_gene=0x%04x mutated_gene=0x%04x", vector_count, result_id, child_gene, mutated_gene);
        end else begin
            $display("[TB_PMO_GA_FAMILY] FAIL: err_count=%0d", err_count);
            $fatal(1, "[TB_PMO_GA_FAMILY] Simulation failed.");
        end
        $finish;
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            cand_valid     <= 1'b0;
            cand_id        <= 16'd0;
            cand_latency   <= 32'd0;
            cand_fidelity  <= 16'd0;
            cand_util      <= 16'd0;
            cand_gene      <= 16'd0;
            batch_done     <= 1'b0;
            rand_tiebreak  <= 1'b0;
            req_seen_count <= 0;
            pending_done   <= 1'b0;
        end else begin
            batch_done <= 1'b0;
            cand_valid <= 1'b0;
            if (req_valid) begin
                cand_valid    <= 1'b1;
                cand_gene     <= vec_mem[req_index][95:80];
                cand_id       <= vec_mem[req_index][79:64];
                cand_latency  <= vec_mem[req_index][63:32];
                cand_fidelity <= vec_mem[req_index][31:16];
                cand_util     <= vec_mem[req_index][15:0];
                rand_tiebreak <= req_index[0];
                req_seen_count <= req_seen_count + 1;
                $fwrite(log_fd, "CAND,%0d,%0d,%0d,%0d,%0d,0,0\n", req_index, vec_mem[req_index][79:64], vec_mem[req_index][63:32], vec_mem[req_index][31:16], vec_mem[req_index][15:0]);
                if (req_seen_count + 1 >= vector_count)
                    pending_done <= 1'b1;
            end else begin
                cand_id       <= 16'd0;
                cand_latency  <= 32'd0;
                cand_fidelity <= 16'd0;
                cand_util     <= 16'd0;
                cand_gene     <= 16'd0;
                rand_tiebreak <= 1'b0;
            end

            if (pending_done) begin
                batch_done   <= 1'b1;
                pending_done <= 1'b0;
            end
        end
    end
endmodule
