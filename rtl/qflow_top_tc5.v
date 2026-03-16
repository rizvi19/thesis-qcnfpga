`timescale 1ns/1ps

module qflow_top_tc5 #(
    parameter integer ADDR_W = 12
) (
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 seed_valid_i,
    input  wire [63:0]          seed0_i,
    input  wire [63:0]          seed1_i,
    input  wire                 prng_enable_i,
    output wire [63:0]          rand_o,
    output wire                 rand_valid_o,
    output wire                 seeded_o,
    input  wire                 cfg_we_i,
    input  wire [ADDR_W-1:0]    cfg_addr_i,
    input  wire [63:0]          cfg_wdata_i,
    input  wire                 fdpe_launch_i,
    input  wire [ADDR_W-1:0]    fdpe_addr_i,
    input  wire [16:0]          fdpe_x_q4_13_i,
    input  wire [15:0]          fdpe_f_init_q016_i,
    output wire                 fdpe_result_valid_o,
    output wire [15:0]          fdpe_result_q016_o,
    output wire                 fdpe_done_o,
    input  wire                 skag_ga_rd_en_i,
    input  wire [ADDR_W-1:0]    skag_ga_rd_addr_i,
    output wire [63:0]          skag_ga_edge_o,
    output wire [31:0]          skag_ga_weight_o,
    output wire                 skag_ga_valid_o,
    input  wire                 ga_start_i,
    input  wire [3:0]           ga_pop_size_i,
    input  wire [3:0]           ga_gen_count_i,
    input  wire                 cand_valid_i,
    input  wire [15:0]          cand_id_i,
    input  wire [31:0]          cand_latency_i,
    input  wire [15:0]          cand_fidelity_i,
    input  wire [15:0]          cand_util_i,
    input  wire [15:0]          cand_gene_i,
    output wire                 req_valid_o,
    output wire [3:0]           req_gen_o,
    output wire [3:0]           req_index_o,
    output wire                 ga_result_valid_o,
    output wire [15:0]          ga_best_id_o,
    output wire [31:0]          ga_best_latency_o,
    output wire [15:0]          ga_best_fidelity_o,
    output wire [15:0]          ga_best_util_o,
    output wire [15:0]          ga_child_gene_o,
    output wire [15:0]          ga_mutated_gene_o
);
    localparam [15:0] ALPHA1_Q8_8 = 16'd256;
    localparam [15:0] ALPHA2_Q8_8 = 16'd384;
    localparam [15:0] ALPHA3_Q8_8 = 16'd128;
    localparam [15:0] ALPHA4_Q8_8 = 16'd512;

    xorshift128plus u_prng (
        .clk(clk), .rst_n(rst_n), .seed_valid_i(seed_valid_i), .seed0_i(seed0_i), .seed1_i(seed1_i),
        .enable_i(prng_enable_i), .rand_o(rand_o), .valid_o(rand_valid_o), .seeded_o(seeded_o)
    );

    wire fdpe_valid_w;
    wire [15:0] fdpe_fidelity_w;
    fdpe_tc5 u_fdpe (
        .clk(clk), .rst_n(rst_n), .valid_i(fdpe_launch_i), .x_q4_13_i(fdpe_x_q4_13_i),
        .f_init_q016_i(fdpe_f_init_q016_i), .valid_o(fdpe_valid_w), .fidelity_q016_o(fdpe_fidelity_w)
    );
    assign fdpe_result_valid_o = fdpe_valid_w;
    assign fdpe_result_q016_o  = fdpe_fidelity_w;

    reg [ADDR_W-1:0] fdpe_addr_d0, fdpe_addr_d1, fdpe_addr_d2, fdpe_addr_d3;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fdpe_addr_d0 <= {ADDR_W{1'b0}};
            fdpe_addr_d1 <= {ADDR_W{1'b0}};
            fdpe_addr_d2 <= {ADDR_W{1'b0}};
            fdpe_addr_d3 <= {ADDR_W{1'b0}};
        end else begin
            if (fdpe_launch_i) fdpe_addr_d0 <= fdpe_addr_i;
            fdpe_addr_d1 <= fdpe_addr_d0;
            fdpe_addr_d2 <= fdpe_addr_d1;
            fdpe_addr_d3 <= fdpe_addr_d2;
        end
    end

    wire [31:0] skag_fdpe_weight_w;
    skag_mem_tc4 #(.ADDR_W(ADDR_W), .DEPTH(1 << ADDR_W)) u_skag (
        .clk(clk), .rst_n(rst_n), .cfg_we_i(cfg_we_i), .cfg_addr_i(cfg_addr_i), .cfg_wdata_i(cfg_wdata_i),
        .fdpe_upd_valid_i(fdpe_valid_w), .fdpe_addr_i(fdpe_addr_d3), .fdpe_fidelity_i(fdpe_fidelity_w),
        .alpha1_q8_8_i(ALPHA1_Q8_8), .alpha2_q8_8_i(ALPHA2_Q8_8), .alpha3_q8_8_i(ALPHA3_Q8_8), .alpha4_q8_8_i(ALPHA4_Q8_8),
        .ga_rd_en_i(skag_ga_rd_en_i), .ga_rd_addr_i(skag_ga_rd_addr_i),
        .ga_rd_edge_o(skag_ga_edge_o), .ga_rd_weight_o(skag_ga_weight_o), .ga_rd_valid_o(skag_ga_valid_o),
        .fdpe_done_o(fdpe_done_o), .fdpe_weight_o(skag_fdpe_weight_w)
    );

    pmo_ga_multigen #(.INDEX_W(4), .GEN_W(4)) u_pmo_ga (
        .clk(clk), .rst_n(rst_n), .start_i(ga_start_i), .pop_size_i(ga_pop_size_i), .gen_count_i(ga_gen_count_i),
        .cand_valid_i(cand_valid_i), .cand_id_i(cand_id_i), .cand_latency_i(cand_latency_i),
        .cand_fidelity_i(cand_fidelity_i), .cand_util_i(cand_util_i), .cand_gene_i(cand_gene_i),
        .req_valid_o(req_valid_o), .req_gen_o(req_gen_o), .req_index_o(req_index_o), .result_valid_o(ga_result_valid_o),
        .best_id_o(ga_best_id_o), .best_latency_o(ga_best_latency_o), .best_fidelity_o(ga_best_fidelity_o),
        .best_util_o(ga_best_util_o), .final_child_gene_o(ga_child_gene_o), .final_mutated_gene_o(ga_mutated_gene_o)
    );
endmodule
