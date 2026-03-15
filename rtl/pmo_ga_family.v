`timescale 1ns/1ps

module pmo_ga_family #(
    parameter integer INDEX_W = 6
) (
    input  wire                clk,
    input  wire                rst_n,
    input  wire                start_i,
    input  wire [INDEX_W-1:0]  pop_size_i,
    input  wire                batch_done_i,
    input  wire                cand_valid_i,
    input  wire [15:0]         cand_id_i,
    input  wire [31:0]         cand_latency_i,
    input  wire [15:0]         cand_fidelity_i,
    input  wire [15:0]         cand_util_i,
    input  wire [15:0]         cand_gene_i,
    input  wire                rand_tiebreak_i,
    output wire                req_valid_o,
    output wire [INDEX_W-1:0]  req_index_o,
    output wire                issue_done_o,
    output wire                result_valid_o,
    output wire [15:0]         result_id_o,
    output wire [31:0]         result_latency_o,
    output wire [15:0]         result_fidelity_o,
    output wire [15:0]         result_util_o,
    output wire [15:0]         child_gene_o,
    output wire [15:0]         mutated_gene_o
);
    wire clear_elite;
    wire fit_valid;
    wire [15:0] fit_id, fit_fidelity, fit_util, fit_gene;
    wire [31:0] fit_latency;
    wire elite_best_valid_unused;

    reg [15:0] parent_a_gene_r, parent_b_gene_r;
    reg [1:0]  parent_count_r;

    ga_init #(.POP_MAX(64), .INDEX_W(INDEX_W)) u_init (
        .clk(clk), .rst_n(rst_n), .start_i(start_i), .ready_i(1'b1), .pop_size_i(pop_size_i),
        .req_valid_o(req_valid_o), .req_index_o(req_index_o), .issue_done_o(issue_done_o)
    );

    ga_controller u_ctrl (
        .clk(clk), .rst_n(rst_n), .start_i(start_i), .batch_done_i(batch_done_i),
        .clear_elite_o(clear_elite), .result_valid_o(result_valid_o)
    );

    ga_fitness u_fit (
        .clk(clk), .rst_n(rst_n), .cand_valid_i(cand_valid_i), .cand_id_i(cand_id_i),
        .cand_latency_i(cand_latency_i), .cand_fidelity_i(cand_fidelity_i), .cand_util_i(cand_util_i),
        .cand_gene_i(cand_gene_i), .fit_valid_o(fit_valid), .fit_id_o(fit_id), .fit_latency_o(fit_latency),
        .fit_fidelity_o(fit_fidelity), .fit_util_o(fit_util), .fit_gene_o(fit_gene)
    );

    ga_elitism u_elite (
        .clk(clk), .rst_n(rst_n), .clear_i(clear_elite), .cand_valid_i(fit_valid), .cand_id_i(fit_id),
        .cand_latency_i(fit_latency), .cand_fidelity_i(fit_fidelity), .cand_util_i(fit_util),
        .rand_tiebreak_i(rand_tiebreak_i), .best_valid_o(elite_best_valid_unused), .best_id_o(result_id_o),
        .best_latency_o(result_latency_o), .best_fidelity_o(result_fidelity_o), .best_util_o(result_util_o)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            parent_a_gene_r <= 16'd0;
            parent_b_gene_r <= 16'd0;
            parent_count_r  <= 2'd0;
        end else if (clear_elite) begin
            parent_a_gene_r <= 16'd0;
            parent_b_gene_r <= 16'd0;
            parent_count_r  <= 2'd0;
        end else if (cand_valid_i) begin
            if (parent_count_r == 2'd0) begin
                parent_a_gene_r <= cand_gene_i;
                parent_count_r  <= 2'd1;
            end else if (parent_count_r == 2'd1) begin
                parent_b_gene_r <= cand_gene_i;
                parent_count_r  <= 2'd2;
            end
        end
    end

    ga_crossover u_cross (
        .parent_a_gene_i(parent_a_gene_r),
        .parent_b_gene_i(parent_b_gene_r),
        .enable_i(parent_count_r == 2'd2),
        .child_gene_o(child_gene_o)
    );

    ga_mutate u_mut (
        .gene_i(child_gene_o),
        .mutate_mask_i(16'h0004),
        .enable_i(parent_count_r == 2'd2),
        .gene_o(mutated_gene_o)
    );
endmodule
