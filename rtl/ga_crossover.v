module ga_crossover (
    input  wire [15:0] parent_a_gene_i,
    input  wire [15:0] parent_b_gene_i,
    input  wire        enable_i,
    output wire [15:0] child_gene_o
);
    assign child_gene_o = enable_i ? {parent_a_gene_i[15:8], parent_b_gene_i[7:0]} : parent_a_gene_i;
endmodule
