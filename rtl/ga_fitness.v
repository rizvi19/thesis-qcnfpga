module ga_fitness (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        cand_valid_i,
    input  wire [15:0] cand_id_i,
    input  wire [31:0] cand_latency_i,
    input  wire [15:0] cand_fidelity_i,
    input  wire [15:0] cand_util_i,
    input  wire [15:0] cand_gene_i,
    output reg         fit_valid_o,
    output reg  [15:0] fit_id_o,
    output reg  [31:0] fit_latency_o,
    output reg  [15:0] fit_fidelity_o,
    output reg  [15:0] fit_util_o,
    output reg  [15:0] fit_gene_o
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fit_valid_o    <= 1'b0;
            fit_id_o       <= 16'd0;
            fit_latency_o  <= 32'd0;
            fit_fidelity_o <= 16'd0;
            fit_util_o     <= 16'd0;
            fit_gene_o     <= 16'd0;
        end else begin
            fit_valid_o    <= cand_valid_i;
            fit_id_o       <= cand_id_i;
            fit_latency_o  <= cand_latency_i;
            fit_fidelity_o <= cand_fidelity_i;
            fit_util_o     <= cand_util_i;
            fit_gene_o     <= cand_gene_i;
        end
    end
endmodule
