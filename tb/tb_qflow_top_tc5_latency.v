`timescale 1ps/1ps
module tb_qflow_top_tc5_latency;

    localparam integer ADDR_W = 12;
    localparam integer POP_SIZE = 8;
    localparam integer GEN_COUNT = 3;
    localparam integer TOTAL_VECTORS = POP_SIZE * GEN_COUNT;
    localparam integer CLK_HALF_PS = 5000;   // 10 ns clock period => 100 MHz
    localparam real    CLOCK_PERIOD_NS = 10.0;

    reg clk = 1'b0;
    reg rst_n = 1'b0;

    reg seed_valid;
    reg [63:0] seed0, seed1;
    reg prng_enable;

    reg cfg_we;
    reg [ADDR_W-1:0] cfg_addr;
    reg [63:0] cfg_wdata;

    reg fdpe_launch;
    reg [ADDR_W-1:0] fdpe_addr;
    reg [16:0] fdpe_x_q4_13;
    reg [15:0] fdpe_f_init;

    reg skag_ga_rd_en;
    reg [ADDR_W-1:0] skag_ga_rd_addr;

    reg ga_start;
    reg [3:0] ga_pop_size;
    reg [3:0] ga_gen_count;

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

    integer summary_fd, csv_fd;
    integer timeout_ctr;

    integer cycle_ctr;
    integer fdpe_start_cycle;
    integer fdpe_valid_cycle;
    integer fdpe_done_cycle;
    integer ga_start_cycle;
    integer ga_result_cycle;

    integer fdpe_cycles;
    integer skag_commit_cycles;
    integer ga_cycles;
    integer end_to_end_cycles;

    real fdpe_latency_ns;
    real skag_commit_latency_ns;
    real ga_latency_ns;
    real end_to_end_latency_ns;

    initial forever #CLK_HALF_PS clk = ~clk;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            cycle_ctr <= 0;
        else
            cycle_ctr <= cycle_ctr + 1;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fdpe_start_cycle <= -1;
            fdpe_valid_cycle <= -1;
            fdpe_done_cycle  <= -1;
            ga_start_cycle   <= -1;
            ga_result_cycle  <= -1;
        end else begin
            if (fdpe_launch && fdpe_start_cycle < 0)
                fdpe_start_cycle <= cycle_ctr;
            if (ga_start && ga_start_cycle < 0)
                ga_start_cycle <= cycle_ctr;
        end
    end

    always @(posedge fdpe_result_valid)
        if (fdpe_valid_cycle < 0) fdpe_valid_cycle = cycle_ctr;

    always @(posedge fdpe_done)
        if (fdpe_done_cycle < 0) fdpe_done_cycle = cycle_ctr;

    always @(posedge ga_result_valid)
        if (ga_result_cycle < 0) ga_result_cycle = cycle_ctr;

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

    qflow_top_tc5 #(.ADDR_W(ADDR_W)) dut (
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
        .ga_pop_size_i(ga_pop_size),
        .ga_gen_count_i(ga_gen_count),
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

    initial begin
        string vectors_file;
        string summary_file;
        string csv_file;
        reg [63:0] init_edge;

        if (!$value$plusargs("VECTORS=%s", vectors_file))
            vectors_file = "tb/qflow_top_tc_candidates.memh";
        if (!$value$plusargs("SUMMARY=%s", summary_file))
            summary_file = "results/phase10_latency/qflow_top_tc5_latency_summary.txt";
        if (!$value$plusargs("CSV=%s", csv_file))
            csv_file = "results/phase10_latency/qflow_top_tc5_latency_metrics.csv";

        $display("[TB_QFLOW_TC5_LAT] vectors=%0s", vectors_file);
        $display("[TB_QFLOW_TC5_LAT] summary=%0s", summary_file);
        $display("[TB_QFLOW_TC5_LAT] csv=%0s", csv_file);

        $readmemh(vectors_file, vec_mem);

        summary_fd = $fopen(summary_file, "w");
        csv_fd = $fopen(csv_file, "w");
        if (summary_fd == 0 || csv_fd == 0) begin
            $display("[TB_QFLOW_TC5_LAT] ERROR: could not open output files.");
            $fatal;
        end

        seed_valid = 0; seed0 = 0; seed1 = 0; prng_enable = 0;
        cfg_we = 0; cfg_addr = 0; cfg_wdata = 0;
        fdpe_launch = 0; fdpe_addr = 0; fdpe_x_q4_13 = 0; fdpe_f_init = 0;
        skag_ga_rd_en = 0; skag_ga_rd_addr = 0;
        ga_start = 0;
        ga_pop_size = 4'd8;
        ga_gen_count = 4'd3;

        fdpe_cycles = -1;
        skag_commit_cycles = -1;
        ga_cycles = -1;
        end_to_end_cycles = -1;

        repeat (3) @(posedge clk);
        rst_n = 1'b1;

        // Seed PRNG once for stable behaviour
        @(posedge clk);
        seed_valid <= 1'b1;
        seed0 <= 64'd1;
        seed1 <= 64'd2;
        @(posedge clk);
        seed_valid <= 1'b0;

        // Configure one SKAG edge
        init_edge = {16'd100, 16'd2000, 16'd63569, 16'd300}; // qber, arrival, fidelity, key_count
        @(posedge clk);
        cfg_we    <= 1'b1;
        cfg_addr  <= 12'd0;
        cfg_wdata <= init_edge;
        @(posedge clk);
        cfg_we    <= 1'b0;
        cfg_addr  <= 12'd0;
        cfg_wdata <= 64'd0;

        // Launch FDPE update
        @(posedge clk);
        fdpe_launch  <= 1'b1;
        fdpe_addr    <= 12'd0;
        fdpe_x_q4_13 <= 17'd8192; // x = 1.0 in Q4.13
        fdpe_f_init  <= 16'd63569;
        @(posedge clk);
        fdpe_launch  <= 1'b0;
        fdpe_addr    <= 12'd0;
        fdpe_x_q4_13 <= 17'd0;
        fdpe_f_init  <= 16'd0;

        timeout_ctr = 0;
        while (!fdpe_result_valid && timeout_ctr < 100) begin
            @(posedge clk);
            timeout_ctr = timeout_ctr + 1;
        end
        if (!fdpe_result_valid) begin
            $display("[TB_QFLOW_TC5_LAT] FAIL: timeout waiting for fdpe_result_valid.");
            $fatal;
        end

        timeout_ctr = 0;
        while (!fdpe_done && timeout_ctr < 100) begin
            @(posedge clk);
            timeout_ctr = timeout_ctr + 1;
        end
        if (!fdpe_done) begin
            $display("[TB_QFLOW_TC5_LAT] FAIL: timeout waiting for fdpe_done.");
            $fatal;
        end

        // Start GA selection path
        @(posedge clk);
        ga_start <= 1'b1;
        @(posedge clk);
        ga_start <= 1'b0;

        timeout_ctr = 0;
        while (!ga_result_valid && timeout_ctr < 300) begin
            @(posedge clk);
            timeout_ctr = timeout_ctr + 1;
        end
        if (!ga_result_valid) begin
            $display("[TB_QFLOW_TC5_LAT] FAIL: timeout waiting for ga_result_valid.");
            $fatal;
        end

        if (fdpe_valid_cycle  < 0) fdpe_valid_cycle  = cycle_ctr;
        if (fdpe_done_cycle   < 0) fdpe_done_cycle   = cycle_ctr;
        if (ga_result_cycle   < 0) ga_result_cycle   = cycle_ctr;

        fdpe_cycles        = fdpe_valid_cycle - fdpe_start_cycle;
        skag_commit_cycles = fdpe_done_cycle - fdpe_start_cycle;
        ga_cycles          = ga_result_cycle - ga_start_cycle;
        end_to_end_cycles  = ga_result_cycle - fdpe_start_cycle;

        fdpe_latency_ns        = fdpe_cycles * CLOCK_PERIOD_NS;
        skag_commit_latency_ns = skag_commit_cycles * CLOCK_PERIOD_NS;
        ga_latency_ns          = ga_cycles * CLOCK_PERIOD_NS;
        end_to_end_latency_ns  = end_to_end_cycles * CLOCK_PERIOD_NS;

        $fwrite(summary_fd, "clock_period_ns=%.3f\n", CLOCK_PERIOD_NS);
        $fwrite(summary_fd, "fdpe_start_cycle=%0d\n", fdpe_start_cycle);
        $fwrite(summary_fd, "fdpe_valid_cycle=%0d\n", fdpe_valid_cycle);
        $fwrite(summary_fd, "fdpe_done_cycle=%0d\n", fdpe_done_cycle);
        $fwrite(summary_fd, "ga_start_cycle=%0d\n", ga_start_cycle);
        $fwrite(summary_fd, "ga_result_cycle=%0d\n", ga_result_cycle);
        $fwrite(summary_fd, "fdpe_cycles=%0d\n", fdpe_cycles);
        $fwrite(summary_fd, "skag_commit_cycles=%0d\n", skag_commit_cycles);
        $fwrite(summary_fd, "ga_cycles=%0d\n", ga_cycles);
        $fwrite(summary_fd, "end_to_end_cycles=%0d\n", end_to_end_cycles);
        $fwrite(summary_fd, "fdpe_latency_ns=%.3f\n", fdpe_latency_ns);
        $fwrite(summary_fd, "skag_commit_latency_ns=%.3f\n", skag_commit_latency_ns);
        $fwrite(summary_fd, "ga_latency_ns=%.3f\n", ga_latency_ns);
        $fwrite(summary_fd, "end_to_end_latency_ns=%.3f\n", end_to_end_latency_ns);
        $fwrite(summary_fd, "ga_best_id=%0d\n", ga_best_id);
        $fwrite(summary_fd, "ga_best_latency=%0d\n", ga_best_latency);
        $fwrite(summary_fd, "ga_best_fidelity=%0d\n", ga_best_fidelity);
        $fwrite(summary_fd, "ga_best_util=%0d\n", ga_best_util);

        $fwrite(csv_fd, "metric_name,cycles,latency_ns\n");
        $fwrite(csv_fd, "fdpe,%0d,%.3f\n", fdpe_cycles, fdpe_latency_ns);
        $fwrite(csv_fd, "skag_commit,%0d,%.3f\n", skag_commit_cycles, skag_commit_latency_ns);
        $fwrite(csv_fd, "ga_selection,%0d,%.3f\n", ga_cycles, ga_latency_ns);
        $fwrite(csv_fd, "end_to_end,%0d,%.3f\n", end_to_end_cycles, end_to_end_latency_ns);

        $fclose(summary_fd);
        $fclose(csv_fd);

        $display("[TB_QFLOW_TC5_LAT] PASS: fdpe=%0d cyc, skag_commit=%0d cyc, ga=%0d cyc, end_to_end=%0d cyc",
                 fdpe_cycles, skag_commit_cycles, ga_cycles, end_to_end_cycles);

        $finish;
    end
endmodule
