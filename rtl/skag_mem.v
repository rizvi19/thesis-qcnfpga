`timescale 1ns/1ps

module skag_mem #(
    parameter integer ADDR_W = 8,
    parameter integer DEPTH  = (1 << ADDR_W)
) (
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 cfg_we_i,
    input  wire [ADDR_W-1:0]    cfg_addr_i,
    input  wire [63:0]          cfg_wdata_i,
    input  wire                 fdpe_upd_valid_i,
    input  wire [ADDR_W-1:0]    fdpe_addr_i,
    input  wire [15:0]          fdpe_fidelity_i,
    input  wire [15:0]          alpha1_q8_8_i,
    input  wire [15:0]          alpha2_q8_8_i,
    input  wire [15:0]          alpha3_q8_8_i,
    input  wire [15:0]          alpha4_q8_8_i,
    input  wire                 ga_rd_en_i,
    input  wire [ADDR_W-1:0]    ga_rd_addr_i,
    output reg  [63:0]          ga_rd_edge_o,
    output reg  [31:0]          ga_rd_weight_o,
    output reg                  ga_rd_valid_o,
    output reg                  fdpe_done_o,
    output reg  [31:0]          fdpe_weight_o
);
    localparam [31:0] INF_WEIGHT = 32'hFFFF_FFFF;

    reg [63:0] edge_mem   [0:DEPTH-1];
    reg [31:0] weight_mem [0:DEPTH-1];

    reg              s0_valid, s1_valid, s2_valid;
    reg [ADDR_W-1:0] s0_addr,  s1_addr,  s2_addr;
    reg [63:0]       s0_edge,  s1_edge,  s2_edge;
    reg [31:0]       s0_weight,s1_weight,s2_weight;

    reg              ga_pending;
    reg              ga_conflict_pending;
    reg [ADDR_W-1:0] ga_addr_d;

    integer i;

    function automatic [31:0] compute_weight;
        input [63:0] edge_i;
        input [15:0] a1_q8_8;
        input [15:0] a2_q8_8;
        input [15:0] a3_q8_8;
        input [15:0] a4_q8_8;
        reg [15:0] key_count;
        reg [15:0] fidelity;
        reg [15:0] arrival_rate;
        reg [15:0] qber;
        reg [63:0] t1;
        reg [63:0] t2;
        reg [63:0] t3;
        reg [63:0] t4;
        reg [63:0] sum;
    begin
        key_count    = edge_i[15:0];
        fidelity     = edge_i[31:16];
        arrival_rate = edge_i[47:32];
        qber         = edge_i[63:48];

        if ((key_count == 16'd0) || (fidelity == 16'd0) || (arrival_rate == 16'd0)) begin
            compute_weight = INF_WEIGHT;
        end else begin
            t1  = ({48'd0, a1_q8_8} << 8)  / key_count;
            t2  = ({48'd0, a2_q8_8} << 24) / fidelity;
            t3  = ({48'd0, a3_q8_8} << 16) / arrival_rate;
            t4  = ({48'd0, a4_q8_8} * qber) >> 8;
            sum = t1 + t2 + t3 + t4;
            if (sum[63:32] != 32'd0)
                compute_weight = INF_WEIGHT;
            else
                compute_weight = sum[31:0];
        end
    end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < DEPTH; i = i + 1) begin
                edge_mem[i]   = 64'd0;
                weight_mem[i] = INF_WEIGHT;
            end

            s0_valid  <= 1'b0; s1_valid  <= 1'b0; s2_valid  <= 1'b0;
            s0_addr   <= {ADDR_W{1'b0}}; s1_addr  <= {ADDR_W{1'b0}}; s2_addr  <= {ADDR_W{1'b0}};
            s0_edge   <= 64'd0; s1_edge  <= 64'd0; s2_edge  <= 64'd0;
            s0_weight <= INF_WEIGHT; s1_weight <= INF_WEIGHT; s2_weight <= INF_WEIGHT;
            ga_pending          <= 1'b0;
            ga_conflict_pending <= 1'b0;
            ga_addr_d           <= {ADDR_W{1'b0}};
            ga_rd_edge_o        <= 64'd0;
            ga_rd_weight_o      <= INF_WEIGHT;
            ga_rd_valid_o       <= 1'b0;
            fdpe_done_o         <= 1'b0;
            fdpe_weight_o       <= INF_WEIGHT;
        end else begin
            fdpe_done_o   <= 1'b0;
            ga_rd_valid_o <= 1'b0;

            if (s2_valid) begin
                edge_mem[s2_addr]   <= s2_edge;
                weight_mem[s2_addr] <= s2_weight;
                fdpe_done_o         <= 1'b1;
                fdpe_weight_o       <= s2_weight;
            end

            if (ga_pending) begin
                if (ga_conflict_pending) begin
                    ga_rd_valid_o  <= 1'b0;
                    ga_rd_edge_o   <= 64'd0;
                    ga_rd_weight_o <= INF_WEIGHT;
                end else begin
                    ga_rd_valid_o  <= 1'b1;
                    ga_rd_edge_o   <= edge_mem[ga_addr_d];
                    ga_rd_weight_o <= weight_mem[ga_addr_d];
                end
            end

            s2_valid  <= s1_valid;
            s2_addr   <= s1_addr;
            s2_edge   <= s1_edge;
            s2_weight <= s1_weight;
            s1_valid  <= s0_valid;
            s1_addr   <= s0_addr;
            s1_edge   <= s0_edge;
            s1_weight <= s0_weight;

            s0_valid  <= fdpe_upd_valid_i;
            s0_addr   <= fdpe_addr_i;
            s0_edge   <= {edge_mem[fdpe_addr_i][63:32], fdpe_fidelity_i, edge_mem[fdpe_addr_i][15:0]};
            s0_weight <= compute_weight({edge_mem[fdpe_addr_i][63:32], fdpe_fidelity_i, edge_mem[fdpe_addr_i][15:0]},
                                        alpha1_q8_8_i, alpha2_q8_8_i, alpha3_q8_8_i, alpha4_q8_8_i);

            if (cfg_we_i && !(fdpe_upd_valid_i && (fdpe_addr_i == cfg_addr_i))) begin
                edge_mem[cfg_addr_i]   <= cfg_wdata_i;
                weight_mem[cfg_addr_i] <= compute_weight(cfg_wdata_i,
                                                         alpha1_q8_8_i, alpha2_q8_8_i,
                                                         alpha3_q8_8_i, alpha4_q8_8_i);
            end

            ga_pending <= ga_rd_en_i;
            ga_addr_d  <= ga_rd_addr_i;
            ga_conflict_pending <= ga_rd_en_i && (
                (fdpe_upd_valid_i && (ga_rd_addr_i == fdpe_addr_i)) ||
                (s0_valid && (ga_rd_addr_i == s0_addr)) ||
                (s1_valid && (ga_rd_addr_i == s1_addr)) ||
                (s2_valid && (ga_rd_addr_i == s2_addr))
            );
        end
    end
endmodule
