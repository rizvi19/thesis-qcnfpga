module ga_mutate (
    input  wire [15:0] gene_i,
    input  wire [15:0] mutate_mask_i,
    input  wire        enable_i,
    output wire [15:0] gene_o
);
    assign gene_o = enable_i ? (gene_i ^ mutate_mask_i) : gene_i;
endmodule
