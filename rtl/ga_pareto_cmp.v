module ga_pareto_cmp (
    input  wire [31:0] latency_a_i,
    input  wire [15:0] fidelity_a_i,
    input  wire [15:0] util_a_i,
    input  wire [31:0] latency_b_i,
    input  wire [15:0] fidelity_b_i,
    input  wire [15:0] util_b_i,
    output wire        a_dominates_o,
    output wire        b_dominates_o
);
    wire a_no_worse = (latency_a_i <= latency_b_i) &&
                      (fidelity_a_i >= fidelity_b_i) &&
                      (util_a_i    <= util_b_i);
    wire b_no_worse = (latency_b_i <= latency_a_i) &&
                      (fidelity_b_i >= fidelity_a_i) &&
                      (util_b_i    <= util_a_i);

    wire a_strict = (latency_a_i < latency_b_i) ||
                    (fidelity_a_i > fidelity_b_i) ||
                    (util_a_i    < util_b_i);
    wire b_strict = (latency_b_i < latency_a_i) ||
                    (fidelity_b_i > fidelity_a_i) ||
                    (util_b_i    < util_a_i);

    assign a_dominates_o = a_no_worse && a_strict;
    assign b_dominates_o = b_no_worse && b_strict;
endmodule
