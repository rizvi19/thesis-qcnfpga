`timescale 1ns/1ps

module tb_skag;
    localparam integer ADDR_W = 8;
    localparam integer MAX_VECTORS = 256;
    localparam integer VEC_W = 208;

    reg clk;
    reg rst_n;

    reg              cfg_we;
    reg [ADDR_W-1:0] cfg_addr;
    reg [63:0]       cfg_wdata;
    reg              fdpe_valid;
    reg [ADDR_W-1:0] fdpe_addr;
    reg [15:0]       fdpe_fidelity;
    reg              ga_rd_en;
    reg [ADDR_W-1:0] ga_rd_addr;

    wire [63:0] ga_rd_edge;
    wire [31:0] ga_rd_weight;
    wire        ga_rd_valid;
    wire        fdpe_done;
    wire [31:0] fdpe_weight;

    reg [15:0] alpha1_q8_8;
    reg [15:0] alpha2_q8_8;
    reg [15:0] alpha3_q8_8;
    reg [15:0] alpha4_q8_8;

    reg [VEC_W-1:0] vec_mem [0:MAX_VECTORS-1];
    reg [VEC_W-1:0] cur_vec;

    integer i;
    integer vector_count;
    integer fail_count;
    integer pass_count;
    integer max_weight_diff;
    integer log_fd;
    reg [1023:0] vectors_file;
    reg [1023:0] log_file;
    reg [1023:0] summary_file;
    integer summary_fd;

    reg exp_ga_valid;
    reg [63:0] exp_ga_edge;
    reg [31:0] exp_ga_weight;
    integer weight_diff;

    skag_mem #(
        .ADDR_W(ADDR_W),
        .DEPTH(1 << ADDR_W)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .cfg_we_i(cfg_we),
        .cfg_addr_i(cfg_addr),
        .cfg_wdata_i(cfg_wdata),
        .fdpe_upd_valid_i(fdpe_valid),
        .fdpe_addr_i(fdpe_addr),
        .fdpe_fidelity_i(fdpe_fidelity),
        .alpha1_q8_8_i(alpha1_q8_8),
        .alpha2_q8_8_i(alpha2_q8_8),
        .alpha3_q8_8_i(alpha3_q8_8),
        .alpha4_q8_8_i(alpha4_q8_8),
        .ga_rd_en_i(ga_rd_en),
        .ga_rd_addr_i(ga_rd_addr),
        .ga_rd_edge_o(ga_rd_edge),
        .ga_rd_weight_o(ga_rd_weight),
        .ga_rd_valid_o(ga_rd_valid),
        .fdpe_done_o(fdpe_done),
        .fdpe_weight_o(fdpe_weight)
    );

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    initial begin
        if (!$value$plusargs("VECTORS=%s", vectors_file))
            vectors_file = "tb/skag_vectors.memh";
        if (!$value$plusargs("LOG=%s", log_file))
            log_file = "results/phase2/skag_sim_results.csv";
        if (!$value$plusargs("SUMMARY=%s", summary_file))
            summary_file = "results/phase2/skag_sim_summary.txt";

        $display("[TB_SKAG] vectors=%0s", vectors_file);
        $display("[TB_SKAG] log=%0s", log_file);
        $display("[TB_SKAG] summary=%0s", summary_file);

        $readmemh(vectors_file, vec_mem);
        vector_count = 0;
        for (i = 0; i < MAX_VECTORS; i = i + 1) begin
            if ((vector_count == i) && (^vec_mem[i] !== 1'bx))
                vector_count = vector_count + 1;
        end

        fail_count = 0;
        pass_count = 0;
        max_weight_diff = 0;

        log_fd = $fopen(log_file, "w");
        if (log_fd == 0) begin
            $display("[TB_SKAG] ERROR: could not open log file.");
            $finish;
        end
        $fdisplay(log_fd, "cycle,cfg_we,cfg_addr,cfg_wdata,fdpe_valid,fdpe_addr,fdpe_fidelity,ga_rd_en,ga_rd_addr,exp_ga_valid,obs_ga_valid,exp_ga_edge,obs_ga_edge,exp_ga_weight,obs_ga_weight,pass");

        cfg_we        = 1'b0;
        cfg_addr      = {ADDR_W{1'b0}};
        cfg_wdata     = 64'd0;
        fdpe_valid    = 1'b0;
        fdpe_addr     = {ADDR_W{1'b0}};
        fdpe_fidelity = 16'd0;
        ga_rd_en      = 1'b0;
        ga_rd_addr    = {ADDR_W{1'b0}};

        alpha1_q8_8 = 16'd256; // 1.0
        alpha2_q8_8 = 16'd384; // 1.5
        alpha3_q8_8 = 16'd128; // 0.5
        alpha4_q8_8 = 16'd512; // 2.0

        rst_n = 1'b0;
        repeat (3) @(posedge clk);
        rst_n = 1'b1;
        @(posedge clk);

        for (i = 0; i < vector_count; i = i + 1) begin
            cur_vec = vec_mem[i];

            cfg_we        = cur_vec[207];
            cfg_addr      = cur_vec[206:199];
            cfg_wdata     = cur_vec[198:135];
            fdpe_valid    = cur_vec[134];
            fdpe_addr     = cur_vec[133:126];
            fdpe_fidelity = cur_vec[125:110];
            ga_rd_en      = cur_vec[109];
            ga_rd_addr    = cur_vec[108:101];
            exp_ga_valid  = cur_vec[100];
            exp_ga_edge   = cur_vec[99:36];
            exp_ga_weight = cur_vec[35:4];

            @(posedge clk);
            #1;

            weight_diff = (ga_rd_weight >= exp_ga_weight) ? (ga_rd_weight - exp_ga_weight) : (exp_ga_weight - ga_rd_weight);
            if (weight_diff > max_weight_diff)
                max_weight_diff = weight_diff;

            if ((ga_rd_valid !== exp_ga_valid) ||
                (exp_ga_valid && ((ga_rd_edge !== exp_ga_edge) || (ga_rd_weight !== exp_ga_weight)))) begin
                fail_count = fail_count + 1;
                $display("[TB_SKAG][MISMATCH] cycle=%0d exp_valid=%0d obs_valid=%0d exp_edge=%h obs_edge=%h exp_weight=%h obs_weight=%h",
                         i, exp_ga_valid, ga_rd_valid, exp_ga_edge, ga_rd_edge, exp_ga_weight, ga_rd_weight);
                $fdisplay(log_fd, "%0d,%0d,%0d,%016h,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%016h,%016h,%08h,%08h,0",
                          i, cfg_we, cfg_addr, cfg_wdata, fdpe_valid, fdpe_addr, fdpe_fidelity, ga_rd_en, ga_rd_addr,
                          exp_ga_valid, ga_rd_valid, exp_ga_edge, ga_rd_edge, exp_ga_weight, ga_rd_weight);
            end else begin
                pass_count = pass_count + 1;
                $fdisplay(log_fd, "%0d,%0d,%0d,%016h,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%016h,%016h,%08h,%08h,1",
                          i, cfg_we, cfg_addr, cfg_wdata, fdpe_valid, fdpe_addr, fdpe_fidelity, ga_rd_en, ga_rd_addr,
                          exp_ga_valid, ga_rd_valid, exp_ga_edge, ga_rd_edge, exp_ga_weight, ga_rd_weight);
            end
        end

        $fclose(log_fd);

        summary_fd = $fopen(summary_file, "w");
        $fdisplay(summary_fd, "SKAG simulation summary");
        $fdisplay(summary_fd, "vector_count=%0d", vector_count);
        $fdisplay(summary_fd, "pass_count=%0d", pass_count);
        $fdisplay(summary_fd, "fail_count=%0d", fail_count);
        $fdisplay(summary_fd, "max_weight_diff=%0d", max_weight_diff);
        $fclose(summary_fd);

        if (fail_count == 0)
            $display("[TB_SKAG] PASS: vectors=%0d max_weight_diff=%0d", vector_count, max_weight_diff);
        else begin
            $display("[TB_SKAG] FAIL: fails=%0d max_weight_diff=%0d", fail_count, max_weight_diff);
            $fatal(1, "[TB_SKAG] Simulation failed.");
        end

        $finish;
    end
endmodule
