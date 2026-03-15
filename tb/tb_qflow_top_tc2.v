`timescale 1ps/1ps
module tb_qflow_top_tc22;
    localparam integer POP_SIZE = 8;
    localparam integer GEN_COUNT = 3;
    localparam integer TOTAL_VECTORS = POP_SIZE * GEN_COUNT;

    reg clk = 1'b0;
    reg rst_n = 1'b0;

    // Top controls
    reg seed_valid;
    reg [63:0] seed0, seed1;
    reg prng_enable;

    reg cfg_we;
    reg [7:0] cfg_addr;
    reg [63:0] cfg_wdata;

    reg fdpe_launch;
    reg [7:0] fdpe_addr;
    reg [16:0] fdpe_x_q4_13;
    reg [15:0] fdpe_f_init;

    reg skag_ga_rd_en;
    reg [7:0] skag_ga_rd_addr;

    reg ga_start;

    wire [63:0] rand_o;
    wire rand_valid;
    wire seeded;

    wire fdpe_result_valid;
    wire [15:0] fdpe_result;
    wire fdpe_done;

    wire [63:0] skag_ga_edge;
    wire [31:0] skag_ga_weight;
    wire skag_ga_valid;

    wire req_valid;
    wire [3:0] req_gen;
    wire [3:0] req_index;
    wire ga_result_valid;
    wire [15:0] ga_best_id;
    wire [31:0] ga_best_latency;
    wire [15:0] ga_best_fidelity;
    wire [15:0] ga_best_util;
    wire [15:0] ga_child_gene;
    wire [15:0] ga_mutated_gene;

    reg         cand_valid;
    reg [15:0]  cand_id;
    reg [31:0]  cand_latency;
    reg [15:0]  cand_fidelity;
    reg [15:0]  cand_util;
    reg [15:0]  cand_gene;

    reg [95:0] vec_mem [0:TOTAL_VECTORS-1];
    integer vec_idx;

    integer log_fd, summary_fd;
    integer fail_count;
    integer timeout_ctr;
    integer prng_samples;

    reg [63:0] last_rand;
    reg [15:0] captured_fdpe_result;
    reg [63:0] captured_skag_edge;
    reg [31:0] captured_skag_weight;

    reg [15:0] exp_best_id;
    reg [31:0] exp_best_latency;
    reg [15:0] exp_best_fidelity;
    reg [15:0] exp_best_util;
    reg [15:0] exp_child_gene;
    reg [15:0] exp_mutated_gene;

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

    function automatic [31:0] compute_weight;
        input [63:0] edge_i;
        reg [15:0] key_count;
        reg [15:0] fidelity;
        reg [15:0] arrival_rate;
        reg [15:0] qber;
        reg [63:0] t1;
        reg [63:0] t2;
        reg [63:0] t3;
        reg [63:0] t4;
        reg [63:0] sum;
    begin
        key_count    = edge_i[15:0];
        fidelity     = edge_i[31:16];
        arrival_rate = edge_i[47:32];
        qber         = edge_i[63:48];
        if ((key_count == 16'd0) || (fidelity == 16'd0) || (arrival_rate == 16'd0)) begin
            compute_weight = 32'hFFFF_FFFF;
        end else begin
            t1  = ({48'd0, 16'd256} << 8)  / key_count;
            t2  = ({48'd0, 16'd384} << 24) / fidelity;
            t3  = ({48'd0, 16'd128} << 16) / arrival_rate;
            t4  = ({48'd0, 16'd512} * qber) >> 8;
            sum = t1 + t2 + t3 + t4;
            compute_weight = (sum[63:32] != 32'd0) ? 32'hFFFF_FFFF : sum[31:0];
        end
    end
    endfunction

    qflow_top_tc2 dut (
        .clk(clk),
        .rst_n(rst_n),
        .seed_valid_i(seed_valid),
        .seed0_i(seed0),
        .seed1_i(seed1),
        .prng_enable_i(prng_enable),
        .rand_o(rand_o),
        .rand_valid_o(rand_valid),
        .seeded_o(seeded),
        .cfg_we_i(cfg_we),
        .cfg_addr_i(cfg_addr),
        .cfg_wdata_i(cfg_wdata),
        .fdpe_launch_i(fdpe_launch),
        .fdpe_addr_i(fdpe_addr),
        .fdpe_x_q4_13_i(fdpe_x_q4_13),
        .fdpe_f_init_q016_i(fdpe_f_init),
        .fdpe_result_valid_o(fdpe_result_valid),
        .fdpe_result_q016_o(fdpe_result),
        .fdpe_done_o(fdpe_done),
        .skag_ga_rd_en_i(skag_ga_rd_en),
        .skag_ga_rd_addr_i(skag_ga_rd_addr),
        .skag_ga_edge_o(skag_ga_edge),
        .skag_ga_weight_o(skag_ga_weight),
        .skag_ga_valid_o(skag_ga_valid),
        .ga_start_i(ga_start),
        .ga_pop_size_i(4'd8),
        .ga_gen_count_i(4'd3),
        .cand_valid_i(cand_valid),
        .cand_id_i(cand_id),
        .cand_latency_i(cand_latency),
        .cand_fidelity_i(cand_fidelity),
        .cand_util_i(cand_util),
        .cand_gene_i(cand_gene),
        .req_valid_o(req_valid),
        .req_gen_o(req_gen),
        .req_index_o(req_index),
        .ga_result_valid_o(ga_result_valid),
        .ga_best_id_o(ga_best_id),
        .ga_best_latency_o(ga_best_latency),
        .ga_best_fidelity_o(ga_best_fidelity),
        .ga_best_util_o(ga_best_util),
        .ga_child_gene_o(ga_child_gene),
        .ga_mutated_gene_o(ga_mutated_gene)
    );

    initial forever #5000 clk = ~clk;

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
        reg [63:0] init_edge;
        reg [63:0] expected_edge;

        if (!$value$plusargs("VECTORS=%s", vectors_file))
            vectors_file = "tb/qflow_top_tc2_candidates.memh";
        if (!$value$plusargs("LOG=%s", log_file))
            log_file = "results/phase9d/qflow_top_tc2_smoke_results.csv";
        if (!$value$plusargs("SUMMARY=%s", summary_file))
            summary_file = "results/phase9d/qflow_top_tc2_smoke_summary.txt";

        $display("[TB_QFLOW_TC2] vectors=%0s", vectors_file);
        $display("[TB_QFLOW_TC2] log=%0s", log_file);
        $display("[TB_QFLOW_TC2] summary=%0s", summary_file);
        $readmemh(vectors_file, vec_mem);

        exp_best_id       = vec_mem[0][95:80];
        exp_best_latency  = vec_mem[0][79:48];
        exp_best_fidelity = vec_mem[0][47:32];
        exp_best_util     = vec_mem[0][31:16];
        for (integer i = 1; i < TOTAL_VECTORS; i = i + 1) begin
            prefer(exp_best_id, exp_best_latency, exp_best_fidelity, exp_best_util,
                   vec_mem[i][95:80], vec_mem[i][79:48], vec_mem[i][47:32], vec_mem[i][31:16],
                   tmp_id, tmp_lat, tmp_fid, tmp_util);
            exp_best_id       = tmp_id;
            exp_best_latency  = tmp_lat;
            exp_best_fidelity = tmp_fid;
            exp_best_util     = tmp_util;
        end
        exp_child_gene   = {vec_mem[TOTAL_VECTORS-POP_SIZE][15:8], vec_mem[TOTAL_VECTORS-POP_SIZE+1][7:0]};
        exp_mutated_gene = exp_child_gene ^ 16'h0005;

        log_fd = $fopen(log_file, "w");
        summary_fd = $fopen(summary_file, "w");
        if (log_fd == 0 || summary_fd == 0) begin
            $display("[TB_QFLOW_TC2] ERROR: could not open output files.");
            $fatal;
        end
        $fwrite(log_fd, "prng_last,fdpe_result,skag_edge,skag_weight,best_id,best_latency,best_fidelity,best_util,child_gene,mutated_gene,pass\n");

        // Defaults
        seed_valid = 0; seed0 = 0; seed1 = 0; prng_enable = 0;
        cfg_we = 0; cfg_addr = 0; cfg_wdata = 0;
        fdpe_launch = 0; fdpe_addr = 0; fdpe_x_q4_13 = 0; fdpe_f_init = 0;
        skag_ga_rd_en = 0; skag_ga_rd_addr = 0;
        ga_start = 0;
        fail_count = 0;
        prng_samples = 0;
        last_rand = 64'd0;
        captured_fdpe_result = 16'd0;
        captured_skag_edge = 64'd0;
        captured_skag_weight = 32'd0;

        repeat (3) @(posedge clk);
        rst_n = 1'b1;

        // ---- PRNG seed + 4 samples ----
        @(posedge clk);
        seed_valid <= 1'b1;
        seed0 <= 64'd1;
        seed1 <= 64'd2;
        @(posedge clk);
        seed_valid <= 1'b0;
        prng_enable <= 1'b1;
        while (prng_samples < 4) begin
            @(posedge clk);
            if (rand_valid) begin
                prng_samples = prng_samples + 1;
                last_rand = rand_o;
            end
        end
        prng_enable <= 1'b0;
        if (!seeded || (last_rand == 64'd0))
            fail_count = fail_count + 1;

        // ---- Configure SKAG edge at address 0 ----
        init_edge = {16'd100, 16'd2000, 16'd63569, 16'd300}; // qber, arrival, fidelity, key_count
        @(posedge clk);
        cfg_we   <= 1'b1;
        cfg_addr <= 8'd0;
        cfg_wdata<= init_edge;
        @(posedge clk);
        cfg_we   <= 1'b0;

        // ---- Launch FDPE for x=1.0 on same edge ----
        @(posedge clk);
        fdpe_launch  <= 1'b1;
        fdpe_addr    <= 8'd0;
        fdpe_x_q4_13 <= 17'd8192;   // 1.0 in Q4.13
        fdpe_f_init  <= 16'd63569;
        @(posedge clk);
        fdpe_launch  <= 1'b0;
        fdpe_addr    <= 8'd0;
        fdpe_x_q4_13 <= 17'd0;
        fdpe_f_init  <= 16'd0;

        timeout_ctr = 0;
        while (!fdpe_result_valid && timeout_ctr < 40) begin
            @(posedge clk);
            timeout_ctr = timeout_ctr + 1;
        end
        if (!fdpe_result_valid) begin
            $display("[TB_QFLOW_TC2] FAIL: timeout waiting for FDPE result.");
            $fatal;
        end
        captured_fdpe_result = fdpe_result;
        if ((fdpe_result < 16'd23383) || (fdpe_result > 16'd23387))
            fail_count = fail_count + 1;

        timeout_ctr = 0;
        while (!fdpe_done && timeout_ctr < 40) begin
            @(posedge clk);
            timeout_ctr = timeout_ctr + 1;
        end
        if (!fdpe_done) begin
            $display("[TB_QFLOW_TC2] FAIL: timeout waiting for SKAG commit.");
            $fatal;
        end

        // ---- Read back SKAG updated edge ----
        @(posedge clk);
        skag_ga_rd_en   <= 1'b1;
        skag_ga_rd_addr <= 8'd0;
        @(posedge clk);
        skag_ga_rd_en   <= 1'b0;
        skag_ga_rd_addr <= 8'd0;

        timeout_ctr = 0;
        while (!skag_ga_valid && timeout_ctr < 20) begin
            @(posedge clk);
            timeout_ctr = timeout_ctr + 1;
        end
        if (!skag_ga_valid) begin
            $display("[TB_QFLOW_TC2] FAIL: timeout waiting for SKAG GA read.");
            $fatal;
        end

        captured_skag_edge = skag_ga_edge;
        captured_skag_weight = skag_ga_weight;
        expected_edge = {16'd100, 16'd2000, captured_fdpe_result, 16'd300};
        if (captured_skag_edge !== expected_edge)
            fail_count = fail_count + 1;
        if (captured_skag_weight !== compute_weight(expected_edge))
            fail_count = fail_count + 1;

        // ---- Start PMO-GA multigen stream ----
        @(posedge clk);
        ga_start <= 1'b1;
        @(posedge clk);
        ga_start <= 1'b0;

        timeout_ctr = 0;
        while (!ga_result_valid && timeout_ctr < 200) begin
            @(posedge clk);
            timeout_ctr = timeout_ctr + 1;
        end
        if (!ga_result_valid) begin
            $display("[TB_QFLOW_TC2] FAIL: timeout waiting for PMO-GA multigen result.");
            $fatal;
        end

        if (ga_best_id !== exp_best_id || ga_best_latency !== exp_best_latency ||
            ga_best_fidelity !== exp_best_fidelity || ga_best_util !== exp_best_util ||
            ga_child_gene !== exp_child_gene || ga_mutated_gene !== exp_mutated_gene)
            fail_count = fail_count + 1;

        $fwrite(log_fd, "0x%016x,%0d,0x%016x,0x%08x,%0d,%0d,%0d,%0d,0x%04x,0x%04x,%0d\n",
                last_rand, captured_fdpe_result, captured_skag_edge, captured_skag_weight,
                ga_best_id, ga_best_latency, ga_best_fidelity, ga_best_util,
                ga_child_gene, ga_mutated_gene, (fail_count == 0));

        $fwrite(summary_fd, "prng_samples=%0d\n", prng_samples);
        $fwrite(summary_fd, "last_rand=0x%016x\n", last_rand);
        $fwrite(summary_fd, "fdpe_result=%0d\n", captured_fdpe_result);
        $fwrite(summary_fd, "skag_edge=0x%016x\n", captured_skag_edge);
        $fwrite(summary_fd, "skag_weight=0x%08x\n", captured_skag_weight);
        $fwrite(summary_fd, "best_id=%0d\n", ga_best_id);
        $fwrite(summary_fd, "best_latency=%0d\n", ga_best_latency);
        $fwrite(summary_fd, "best_fidelity=%0d\n", ga_best_fidelity);
        $fwrite(summary_fd, "best_util=%0d\n", ga_best_util);
        $fwrite(summary_fd, "child_gene=0x%04x\n", ga_child_gene);
        $fwrite(summary_fd, "mutated_gene=0x%04x\n", ga_mutated_gene);
        $fwrite(summary_fd, "fail_count=%0d\n", fail_count);
        $fwrite(summary_fd, "overall_pass=%0s\n", (fail_count == 0) ? "true" : "false");

        $fclose(log_fd);
        $fclose(summary_fd);

        if (fail_count == 0) begin
            $display("[TB_QFLOW_TC2] PASS: fdpe=%0d skag_weight=0x%08x best_id=%0d child_gene=0x%04x mutated_gene=0x%04x",
                     captured_fdpe_result, captured_skag_weight, ga_best_id, ga_child_gene, ga_mutated_gene);
        end else begin
            $display("[TB_QFLOW_TC2] FAIL: mismatches=%0d", fail_count);
            $fatal;
        end
        $finish;
    end
endmodule
