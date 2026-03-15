module ga_select (
    input  wire [15:0] cand_a_id_i,
    input  wire [31:0] cand_a_latency_i,
    input  wire [15:0] cand_a_fidelity_i,
    input  wire [15:0] cand_a_util_i,
    input  wire [15:0] cand_b_id_i,
    input  wire [31:0] cand_b_latency_i,
    input  wire [15:0] cand_b_fidelity_i,
    input  wire [15:0] cand_b_util_i,
    input  wire        rand_tiebreak_i,
    output reg  [15:0] winner_id_o,
    output reg  [31:0] winner_latency_o,
    output reg  [15:0] winner_fidelity_o,
    output reg  [15:0] winner_util_o
);
    wire a_dom, b_dom;

    ga_pareto_cmp u_cmp (
        .latency_a_i(cand_a_latency_i),
        .fidelity_a_i(cand_a_fidelity_i),
        .util_a_i(cand_a_util_i),
        .latency_b_i(cand_b_latency_i),
        .fidelity_b_i(cand_b_fidelity_i),
        .util_b_i(cand_b_util_i),
        .a_dominates_o(a_dom),
        .b_dominates_o(b_dom)
    );

    always @(*) begin
        if (a_dom) begin
            winner_id_o       = cand_a_id_i;
            winner_latency_o  = cand_a_latency_i;
            winner_fidelity_o = cand_a_fidelity_i;
            winner_util_o     = cand_a_util_i;
        end else if (b_dom) begin
            winner_id_o       = cand_b_id_i;
            winner_latency_o  = cand_b_latency_i;
            winner_fidelity_o = cand_b_fidelity_i;
            winner_util_o     = cand_b_util_i;
        end else if (cand_a_latency_i < cand_b_latency_i) begin
            winner_id_o       = cand_a_id_i;
            winner_latency_o  = cand_a_latency_i;
            winner_fidelity_o = cand_a_fidelity_i;
            winner_util_o     = cand_a_util_i;
        end else if (cand_b_latency_i < cand_a_latency_i) begin
            winner_id_o       = cand_b_id_i;
            winner_latency_o  = cand_b_latency_i;
            winner_fidelity_o = cand_b_fidelity_i;
            winner_util_o     = cand_b_util_i;
        end else if (cand_a_fidelity_i > cand_b_fidelity_i) begin
            winner_id_o       = cand_a_id_i;
            winner_latency_o  = cand_a_latency_i;
            winner_fidelity_o = cand_a_fidelity_i;
            winner_util_o     = cand_a_util_i;
        end else if (cand_b_fidelity_i > cand_a_fidelity_i) begin
            winner_id_o       = cand_b_id_i;
            winner_latency_o  = cand_b_latency_i;
            winner_fidelity_o = cand_b_fidelity_i;
            winner_util_o     = cand_b_util_i;
        end else if (cand_a_util_i < cand_b_util_i) begin
            winner_id_o       = cand_a_id_i;
            winner_latency_o  = cand_a_latency_i;
            winner_fidelity_o = cand_a_fidelity_i;
            winner_util_o     = cand_a_util_i;
        end else if (cand_b_util_i < cand_a_util_i) begin
            winner_id_o       = cand_b_id_i;
            winner_latency_o  = cand_b_latency_i;
            winner_fidelity_o = cand_b_fidelity_i;
            winner_util_o     = cand_b_util_i;
        end else if (!rand_tiebreak_i) begin
            winner_id_o       = cand_a_id_i;
            winner_latency_o  = cand_a_latency_i;
            winner_fidelity_o = cand_a_fidelity_i;
            winner_util_o     = cand_a_util_i;
        end else begin
            winner_id_o       = cand_b_id_i;
            winner_latency_o  = cand_b_latency_i;
            winner_fidelity_o = cand_b_fidelity_i;
            winner_util_o     = cand_b_util_i;
        end
    end
endmodule
