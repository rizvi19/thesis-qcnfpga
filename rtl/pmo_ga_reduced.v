
module pmo_ga_reduced (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start_i,
    input  wire        cand_valid_i,
    input  wire [15:0] cand_id_i,
    input  wire [31:0] cand_latency_i,
    input  wire [15:0] cand_fidelity_i,
    input  wire [15:0] cand_util_i,
    input  wire        batch_done_i,
    input  wire        rand_tiebreak_i,

    output wire        result_valid_o,
    output wire [15:0] result_id_o,
    output wire [31:0] result_latency_o,
    output wire [15:0] result_fidelity_o,
    output wire [15:0] result_util_o
);
    reg clear_d;
    reg result_valid_r;

    wire best_valid;
    wire [15:0] best_id;
    wire [31:0] best_latency;
    wire [15:0] best_fidelity;
    wire [15:0] best_util;

    ga_elitism u_elite (
        .clk(clk),
        .rst_n(rst_n),
        .clear_i(clear_d),
        .cand_valid_i(cand_valid_i),
        .cand_id_i(cand_id_i),
        .cand_latency_i(cand_latency_i),
        .cand_fidelity_i(cand_fidelity_i),
        .cand_util_i(cand_util_i),
        .rand_tiebreak_i(rand_tiebreak_i),
        .best_valid_o(best_valid),
        .best_id_o(best_id),
        .best_latency_o(best_latency),
        .best_fidelity_o(best_fidelity),
        .best_util_o(best_util)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            clear_d        <= 1'b1;
            result_valid_r <= 1'b0;
        end else begin
            clear_d        <= start_i;
            result_valid_r <= batch_done_i && best_valid;
        end
    end

    assign result_valid_o    = result_valid_r;
    assign result_id_o       = best_id;
    assign result_latency_o  = best_latency;
    assign result_fidelity_o = best_fidelity;
    assign result_util_o     = best_util;
endmodule
