`timescale 1ns/1ps

module pmo_ga_multigen #(
    parameter integer INDEX_W = 4,
    parameter integer GEN_W   = 4
) (
    input  wire                clk,
    input  wire                rst_n,
    input  wire                start_i,
    input  wire [INDEX_W-1:0]  pop_size_i,
    input  wire [GEN_W-1:0]    gen_count_i,
    input  wire                cand_valid_i,
    input  wire [15:0]         cand_id_i,
    input  wire [31:0]         cand_latency_i,
    input  wire [15:0]         cand_fidelity_i,
    input  wire [15:0]         cand_util_i,
    input  wire [15:0]         cand_gene_i,
    output reg                 req_valid_o,
    output reg  [GEN_W-1:0]    req_gen_o,
    output reg  [INDEX_W-1:0]  req_index_o,
    output reg                 result_valid_o,
    output wire [15:0]         best_id_o,
    output wire [31:0]         best_latency_o,
    output wire [15:0]         best_fidelity_o,
    output wire [15:0]         best_util_o,
    output reg  [15:0]         final_child_gene_o,
    output reg  [15:0]         final_mutated_gene_o
);
    localparam [1:0] ST_IDLE  = 2'd0;
    localparam [1:0] ST_CLEAR = 2'd1;
    localparam [1:0] ST_ISSUE = 2'd2;
    localparam [1:0] ST_DONE  = 2'd3;

    reg [1:0] state_r;
    reg       clear_gen_r;
    reg       clear_global_r;
    reg [15:0] parent_a_gene_r, parent_b_gene_r;
    reg [1:0]  parent_count_r;

    wire gen_best_valid;
    wire [15:0] gen_best_id;
    wire [31:0] gen_best_latency;
    wire [15:0] gen_best_fidelity;
    wire [15:0] gen_best_util;
    wire global_best_valid_unused;

    ga_elitism u_gen_elite (
        .clk(clk), .rst_n(rst_n), .clear_i(clear_gen_r), .cand_valid_i(cand_valid_i),
        .cand_id_i(cand_id_i), .cand_latency_i(cand_latency_i), .cand_fidelity_i(cand_fidelity_i),
        .cand_util_i(cand_util_i), .rand_tiebreak_i(1'b0), .best_valid_o(gen_best_valid),
        .best_id_o(gen_best_id), .best_latency_o(gen_best_latency), .best_fidelity_o(gen_best_fidelity),
        .best_util_o(gen_best_util)
    );

    ga_elitism u_global_elite (
        .clk(clk), .rst_n(rst_n), .clear_i(clear_global_r), .cand_valid_i(cand_valid_i),
        .cand_id_i(cand_id_i), .cand_latency_i(cand_latency_i), .cand_fidelity_i(cand_fidelity_i),
        .cand_util_i(cand_util_i), .rand_tiebreak_i(1'b0), .best_valid_o(global_best_valid_unused),
        .best_id_o(best_id_o), .best_latency_o(best_latency_o), .best_fidelity_o(best_fidelity_o),
        .best_util_o(best_util_o)
    );

    wire [15:0] child_gene_w;
    wire [15:0] mutated_gene_w;
    ga_crossover u_cross (
        .parent_a_gene_i(parent_a_gene_r), .parent_b_gene_i(parent_b_gene_r),
        .enable_i(parent_count_r == 2'd2), .child_gene_o(child_gene_w)
    );
    ga_mutate u_mut (
        .gene_i(child_gene_w), .mutate_mask_i(16'h0005),
        .enable_i(parent_count_r == 2'd2), .gene_o(mutated_gene_w)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_r              <= ST_IDLE;
            req_valid_o          <= 1'b0;
            req_gen_o            <= {GEN_W{1'b0}};
            req_index_o          <= {INDEX_W{1'b0}};
            result_valid_o       <= 1'b0;
            clear_gen_r          <= 1'b0;
            clear_global_r       <= 1'b0;
            parent_a_gene_r      <= 16'd0;
            parent_b_gene_r      <= 16'd0;
            parent_count_r       <= 2'd0;
            final_child_gene_o   <= 16'd0;
            final_mutated_gene_o <= 16'd0;
        end else begin
            result_valid_o <= 1'b0;
            clear_gen_r    <= 1'b0;
            clear_global_r <= 1'b0;

            case (state_r)
                ST_IDLE: begin
                    req_valid_o <= 1'b0;
                    req_gen_o   <= {GEN_W{1'b0}};
                    req_index_o <= {INDEX_W{1'b0}};
                    parent_a_gene_r <= 16'd0;
                    parent_b_gene_r <= 16'd0;
                    parent_count_r  <= 2'd0;
                    if (start_i) begin
                        state_r        <= ST_CLEAR;
                        req_gen_o      <= {GEN_W{1'b0}};
                        req_index_o    <= {INDEX_W{1'b0}};
                        clear_gen_r    <= 1'b1;
                        clear_global_r <= 1'b1;
                        final_child_gene_o   <= 16'd0;
                        final_mutated_gene_o <= 16'd0;
                    end
                end

                ST_CLEAR: begin
                    req_valid_o <= 1'b0;
                    parent_a_gene_r <= 16'd0;
                    parent_b_gene_r <= 16'd0;
                    parent_count_r  <= 2'd0;
                    state_r <= ST_ISSUE;
                end

                ST_ISSUE: begin
                    req_valid_o <= 1'b1;
                    if (cand_valid_i) begin
                        if (parent_count_r == 2'd0) begin
                            parent_a_gene_r <= cand_gene_i;
                            parent_count_r  <= 2'd1;
                        end else if (parent_count_r == 2'd1) begin
                            parent_b_gene_r <= cand_gene_i;
                            parent_count_r  <= 2'd2;
                        end

                        if (req_index_o + {{(INDEX_W-1){1'b0}},1'b1} >= pop_size_i) begin
                            final_child_gene_o   <= child_gene_w;
                            final_mutated_gene_o <= mutated_gene_w;
                            req_valid_o <= 1'b0;
                            if (req_gen_o + {{(GEN_W-1){1'b0}},1'b1} >= gen_count_i) begin
                                state_r <= ST_DONE;
                            end else begin
                                state_r     <= ST_CLEAR;
                                req_gen_o   <= req_gen_o + {{(GEN_W-1){1'b0}},1'b1};
                                req_index_o <= {INDEX_W{1'b0}};
                                clear_gen_r <= 1'b1;
                            end
                        end else begin
                            req_index_o <= req_index_o + {{(INDEX_W-1){1'b0}},1'b1};
                        end
                    end
                end

                ST_DONE: begin
                    req_valid_o    <= 1'b0;
                    result_valid_o <= 1'b1;
                    state_r        <= ST_IDLE;
                end

                default: state_r <= ST_IDLE;
            endcase
        end
    end
endmodule
