`timescale 1ps/1ps
module tb_pmo_ga_multigen;
    localparam integer POP_SIZE  = 8;
    localparam integer GEN_COUNT = 3;
    localparam integer TOTAL_VECTORS = POP_SIZE * GEN_COUNT;
    localparam [15:0] MUT_MASK = 16'h0005;

    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg start_i = 1'b0;

    wire req_valid;
    wire [3:0] req_gen;
    wire [3:0] req_index;
    wire result_valid;
    wire [15:0] best_id;
    wire [31:0] best_latency;
    wire [15:0] best_fidelity;
    wire [15:0] best_util;
    wire [15:0] final_child_gene;
    wire [15:0] final_mutated_gene;

    reg         cand_valid;
    reg [15:0]  cand_id;
    reg [31:0]  cand_latency;
    reg [15:0]  cand_fidelity;
    reg [15:0]  cand_util;
    reg [15:0]  cand_gene;

    reg [95:0] vec_mem [0:TOTAL_VECTORS-1];
    integer log_fd;
    integer summary_fd;
    integer timeout_ctr;
    integer i;

    reg [15:0] exp_best_id;
    reg [31:0] exp_best_latency;
    reg [15:0] exp_best_fidelity;
    reg [15:0] exp_best_util;
    reg [15:0] exp_child_gene;
    reg [15:0] exp_mutated_gene;
    integer fail_count;

    function automatic [0:0] a_dom;
        input [31:0] la; input [15:0] fa; input [15:0] ua;
        input [31:0] lb; input [15:0] fb; input [15:0] ub;
        begin
            a_dom = (la <= lb) && (fa >= fb) && (ua <= ub) && ((la < lb) || (fa > fb) || (ua < ub));
        end
    endfunction

    task automatic prefer;
        input [15:0] a_id; input [31:0] a_lat; input [15:0] a_fid; input [15:0] a_util;
        input [15:0] b_id; input [31:0] b_lat; input [15:0] b_fid; input [15:0] b_util;
        output [15:0] w_id; output [31:0] w_lat; output [15:0] w_fid; output [15:0] w_util;
        begin
            if (a_dom(a_lat,a_fid,a_util,b_lat,b_fid,b_util)) begin
                w_id = a_id; w_lat = a_lat; w_fid = a_fid; w_util = a_util;
            end else if (a_dom(b_lat,b_fid,b_util,a_lat,a_fid,a_util)) begin
                w_id = b_id; w_lat = b_lat; w_fid = b_fid; w_util = b_util;
            end else if (a_lat < b_lat) begin
                w_id = a_id; w_lat = a_lat; w_fid = a_fid; w_util = a_util;
            end else if (b_lat < a_lat) begin
                w_id = b_id; w_lat = b_lat; w_fid = b_fid; w_util = b_util;
            end else if (a_fid > b_fid) begin
                w_id = a_id; w_lat = a_lat; w_fid = a_fid; w_util = a_util;
            end else if (b_fid > a_fid) begin
                w_id = b_id; w_lat = b_lat; w_fid = b_fid; w_util = b_util;
            end else if (a_util < b_util) begin
                w_id = a_id; w_lat = a_lat; w_fid = a_fid; w_util = a_util;
            end else begin
                w_id = b_id; w_lat = b_lat; w_fid = b_fid; w_util = b_util;
            end
        end
    endtask

    initial forever #5000 clk = ~clk;

    pmo_ga_multigen #(.INDEX_W(4), .GEN_W(4)) dut (
        .clk(clk), .rst_n(rst_n), .start_i(start_i),
        .pop_size_i(4'd8), .gen_count_i(4'd3),
        .cand_valid_i(cand_valid), .cand_id_i(cand_id), .cand_latency_i(cand_latency),
        .cand_fidelity_i(cand_fidelity), .cand_util_i(cand_util), .cand_gene_i(cand_gene),
        .req_valid_o(req_valid), .req_gen_o(req_gen), .req_index_o(req_index),
        .result_valid_o(result_valid), .best_id_o(best_id), .best_latency_o(best_latency),
        .best_fidelity_o(best_fidelity), .best_util_o(best_util),
        .final_child_gene_o(final_child_gene), .final_mutated_gene_o(final_mutated_gene)
    );

    integer vec_idx;
    always @(*) begin
        cand_valid    = 1'b0;
        cand_id       = 16'd0;
        cand_latency  = 32'd0;
        cand_fidelity = 16'd0;
        cand_util     = 16'd0;
        cand_gene     = 16'd0;
        vec_idx = (req_gen * POP_SIZE) + req_index;
        if (req_valid && (vec_idx < TOTAL_VECTORS)) begin
            cand_valid    = 1'b1;
            cand_id       = vec_mem[vec_idx][95:80];
            cand_latency  = vec_mem[vec_idx][79:48];
            cand_fidelity = vec_mem[vec_idx][47:32];
            cand_util     = vec_mem[vec_idx][31:16];
            cand_gene     = vec_mem[vec_idx][15:0];
        end
    end

    initial begin
        string vectors_file;
        string log_file;
        string summary_file;
        reg [15:0] tmp_id;
        reg [31:0] tmp_lat;
        reg [15:0] tmp_fid;
        reg [15:0] tmp_util;
        reg [15:0] tmp_id2;
        reg [31:0] tmp_lat2;
        reg [15:0] tmp_fid2;
        reg [15:0] tmp_util2;

        if (!$value$plusargs("VECTORS=%s", vectors_file))
            vectors_file = "tb/pmo_ga_multigen_vectors.memh";
        if (!$value$plusargs("LOG=%s", log_file))
            log_file = "results/phase6/pmo_ga_multigen_sim_results.csv";
        if (!$value$plusargs("SUMMARY=%s", summary_file))
            summary_file = "results/phase6/pmo_ga_multigen_sim_summary.txt";

        $display("[TB_PMO_GA_MULTIGEN] vectors=%0s", vectors_file);
        $display("[TB_PMO_GA_MULTIGEN] log=%0s", log_file);
        $display("[TB_PMO_GA_MULTIGEN] summary=%0s", summary_file);
        $readmemh(vectors_file, vec_mem);

        // Compute expected global best from the loaded vectors.
        exp_best_id       = vec_mem[0][95:80];
        exp_best_latency  = vec_mem[0][79:48];
        exp_best_fidelity = vec_mem[0][47:32];
        exp_best_util     = vec_mem[0][31:16];
        for (i = 1; i < TOTAL_VECTORS; i = i + 1) begin
            prefer(exp_best_id, exp_best_latency, exp_best_fidelity, exp_best_util,
                   vec_mem[i][95:80], vec_mem[i][79:48], vec_mem[i][47:32], vec_mem[i][31:16],
                   tmp_id, tmp_lat, tmp_fid, tmp_util);
            exp_best_id       = tmp_id;
            exp_best_latency  = tmp_lat;
            exp_best_fidelity = tmp_fid;
            exp_best_util     = tmp_util;
        end

        exp_child_gene   = {vec_mem[TOTAL_VECTORS-POP_SIZE][15:8], vec_mem[TOTAL_VECTORS-POP_SIZE+1][7:0]};
        exp_mutated_gene = exp_child_gene ^ MUT_MASK;

        log_fd = $fopen(log_file, "w");
        summary_fd = $fopen(summary_file, "w");
        if (log_fd == 0 || summary_fd == 0) begin
            $display("[TB_PMO_GA_MULTIGEN] ERROR: could not open output files.");
            $fatal;
        end
        $fwrite(log_fd, "observed_best_id,observed_latency,observed_fidelity,observed_util,observed_child_gene,observed_mutated_gene,expected_best_id,expected_latency,expected_fidelity,expected_util,expected_child_gene,expected_mutated_gene,pass\n");

        rst_n = 1'b0;
        start_i = 1'b0;
        fail_count = 0;
        timeout_ctr = 0;
        repeat (3) @(posedge clk);
        rst_n = 1'b1;
        @(posedge clk);
        start_i = 1'b1;
        @(posedge clk);
        start_i = 1'b0;

        while (!result_valid && timeout_ctr < 200) begin
            @(posedge clk);
            timeout_ctr = timeout_ctr + 1;
        end

        if (!result_valid) begin
            $display("[TB_PMO_GA_MULTIGEN] FAIL: timeout.");
            $fatal;
        end

        if (best_id !== exp_best_id || best_latency !== exp_best_latency ||
            best_fidelity !== exp_best_fidelity || best_util !== exp_best_util ||
            final_child_gene !== exp_child_gene || final_mutated_gene !== exp_mutated_gene) begin
            fail_count = fail_count + 1;
        end

        $fwrite(log_fd, "%0d,%0d,%0d,%0d,0x%04x,0x%04x,%0d,%0d,%0d,%0d,0x%04x,0x%04x,%0d\n",
                best_id, best_latency, best_fidelity, best_util, final_child_gene, final_mutated_gene,
                exp_best_id, exp_best_latency, exp_best_fidelity, exp_best_util, exp_child_gene, exp_mutated_gene,
                (fail_count == 0));

        $fwrite(summary_fd, "generation_count=%0d\n", GEN_COUNT);
        $fwrite(summary_fd, "vector_count=%0d\n", TOTAL_VECTORS);
        $fwrite(summary_fd, "expected_best_id=%0d\n", exp_best_id);
        $fwrite(summary_fd, "observed_best_id=%0d\n", best_id);
        $fwrite(summary_fd, "observed_latency=%0d\n", best_latency);
        $fwrite(summary_fd, "observed_fidelity=%0d\n", best_fidelity);
        $fwrite(summary_fd, "observed_util=%0d\n", best_util);
        $fwrite(summary_fd, "observed_child_gene=0x%04x\n", final_child_gene);
        $fwrite(summary_fd, "observed_mutated_gene=0x%04x\n", final_mutated_gene);
        $fwrite(summary_fd, "fail_count=%0d\n", fail_count);
        $fwrite(summary_fd, "overall_pass=%0s\n", (fail_count == 0) ? "true" : "false");
        $fclose(log_fd);
        $fclose(summary_fd);

        if (fail_count == 0) begin
            $display("[TB_PMO_GA_MULTIGEN] PASS: vectors=%0d best_id=%0d child_gene=0x%04x mutated_gene=0x%04x",
                TOTAL_VECTORS, best_id, final_child_gene, final_mutated_gene);
        end else begin
            $display("[TB_PMO_GA_MULTIGEN] FAIL: mismatches=%0d", fail_count);
            $fatal;
        end
        $finish;
    end
endmodule
