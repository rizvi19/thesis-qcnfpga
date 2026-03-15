module ga_elitism (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        clear_i,
    input  wire        cand_valid_i,
    input  wire [15:0] cand_id_i,
    input  wire [31:0] cand_latency_i,
    input  wire [15:0] cand_fidelity_i,
    input  wire [15:0] cand_util_i,
    input  wire        rand_tiebreak_i,
    output reg         best_valid_o,
    output reg  [15:0] best_id_o,
    output reg  [31:0] best_latency_o,
    output reg  [15:0] best_fidelity_o,
    output reg  [15:0] best_util_o
);
    wire [15:0] winner_id;
    wire [31:0] winner_latency;
    wire [15:0] winner_fidelity;
    wire [15:0] winner_util;

    ga_select u_select (
        .cand_a_id_i(best_id_o),
        .cand_a_latency_i(best_latency_o),
        .cand_a_fidelity_i(best_fidelity_o),
        .cand_a_util_i(best_util_o),
        .cand_b_id_i(cand_id_i),
        .cand_b_latency_i(cand_latency_i),
        .cand_b_fidelity_i(cand_fidelity_i),
        .cand_b_util_i(cand_util_i),
        .rand_tiebreak_i(rand_tiebreak_i),
        .winner_id_o(winner_id),
        .winner_latency_o(winner_latency),
        .winner_fidelity_o(winner_fidelity),
        .winner_util_o(winner_util)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            best_valid_o    <= 1'b0;
            best_id_o       <= 16'd0;
            best_latency_o  <= 32'd0;
            best_fidelity_o <= 16'd0;
            best_util_o     <= 16'd0;
        end else if (clear_i) begin
            best_valid_o    <= 1'b0;
            best_id_o       <= 16'd0;
            best_latency_o  <= 32'd0;
            best_fidelity_o <= 16'd0;
            best_util_o     <= 16'd0;
        end else if (cand_valid_i) begin
            if (!best_valid_o) begin
                best_valid_o    <= 1'b1;
                best_id_o       <= cand_id_i;
                best_latency_o  <= cand_latency_i;
                best_fidelity_o <= cand_fidelity_i;
                best_util_o     <= cand_util_i;
            end else begin
                best_id_o       <= winner_id;
                best_latency_o  <= winner_latency;
                best_fidelity_o <= winner_fidelity;
                best_util_o     <= winner_util;
            end
        end
    end
endmodule
