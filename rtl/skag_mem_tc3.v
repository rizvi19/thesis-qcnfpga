`timescale 1ns/1ps

module skag_mem_tc3 #(
    parameter integer ADDR_W = 12,
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

    (* ram_style = "block" *) reg [15:0] qber_mem    [0:DEPTH-1];
    (* ram_style = "block" *) reg [15:0] arrival_mem [0:DEPTH-1];
    (* ram_style = "block" *) reg [15:0] key_mem     [0:DEPTH-1];
`ifndef SYNTHESIS
    (* ram_style = "block" *) reg [15:0] fidelity_mem [0:DEPTH-1];
    (* ram_style = "block" *) reg [31:0] weight_mem   [0:DEPTH-1];
    (* ram_style = "block" *) reg [31:0] base_mem     [0:DEPTH-1];
`endif

    reg [15:0] a_qber_dout, a_arrival_dout, a_key_dout;
    reg [15:0] b_qber_dout, b_arrival_dout, b_fidelity_dout, b_key_dout;
    reg [31:0] b_weight_dout;
    reg [31:0] base_dout;

    reg                  fdpe_req_valid;
    reg [ADDR_W-1:0]     fdpe_req_addr;
    reg [15:0]           fdpe_req_fidelity;

    reg                  fdpe_s0_valid;
    reg [ADDR_W-1:0]     fdpe_s0_addr;
    reg [15:0]           fdpe_s0_fidelity;
    reg [31:0]           fdpe_s0_base;

    reg                  fdpe_s1_valid;
    reg [ADDR_W-1:0]     fdpe_s1_addr;
    reg [15:0]           fdpe_s1_new_fidelity;
    reg [31:0]           fdpe_s1_base;
    reg [31:0]           fdpe_s1_dyn_term;

    reg                  fdpe_s2_valid;
    reg [ADDR_W-1:0]     fdpe_s2_addr;
    reg [15:0]           fdpe_s2_new_fidelity;
    reg [31:0]           fdpe_s2_new_weight;

    reg                  fdpe_s3_valid;
    reg [ADDR_W-1:0]     fdpe_s3_addr;
    reg [15:0]           fdpe_s3_new_fidelity;
    reg [31:0]           fdpe_s3_new_weight;

    reg                  fdpe_s4_valid;
    reg [ADDR_W-1:0]     fdpe_s4_addr;
    reg [15:0]           fdpe_s4_new_fidelity;
    reg [31:0]           fdpe_s4_new_weight;

    reg                  ga_pending;
    reg                  ga_conflict_pending;

    wire fdpe_busy = fdpe_req_valid || fdpe_s0_valid || fdpe_s1_valid || fdpe_s2_valid || fdpe_s3_valid || fdpe_s4_valid;
    wire a_use_fdpe_write = fdpe_s4_valid;
    wire a_use_fdpe_read  = (!fdpe_busy) && fdpe_upd_valid_i;
    wire a_use_cfg        = (!a_use_fdpe_write) && (!a_use_fdpe_read) && cfg_we_i;
    wire [ADDR_W-1:0] mem_waddr = a_use_cfg ? cfg_addr_i : fdpe_s4_addr;
    wire mem_we = a_use_cfg || a_use_fdpe_write;

    function [31:0] compute_base;
        input [15:0] key_count;
        input [15:0] arrival_rate;
        input [15:0] qber;
        input [15:0] a1_q8_8;
        input [15:0] a3_q8_8;
        input [15:0] a4_q8_8;
        reg [63:0] t1, t3, t4, sum;
    begin
        if ((key_count == 16'd0) || (arrival_rate == 16'd0)) begin
            compute_base = INF_WEIGHT;
        end else begin
            t1  = ({48'd0, a1_q8_8} << 8)  / key_count;
            t3  = ({48'd0, a3_q8_8} << 16) / arrival_rate;
            t4  = ({48'd0, a4_q8_8} * qber) >> 8;
            sum = t1 + t3 + t4;
            compute_base = (sum[63:32] != 32'd0) ? INF_WEIGHT : sum[31:0];
        end
    end
    endfunction

    function [31:0] compute_fidelity_term;
        input [15:0] fidelity;
        input [15:0] a2_q8_8;
        reg [63:0] t2;
    begin
        if (fidelity == 16'd0) begin
            compute_fidelity_term = INF_WEIGHT;
        end else begin
            t2 = ({48'd0, a2_q8_8} << 24) / fidelity;
            compute_fidelity_term = (t2[63:32] != 32'd0) ? INF_WEIGHT : t2[31:0];
        end
    end
    endfunction

    function [31:0] add_weight_terms;
        input [31:0] base_term;
        input [31:0] dyn_term;
        reg [63:0] sum;
    begin
        if ((base_term == INF_WEIGHT) || (dyn_term == INF_WEIGHT)) begin
            add_weight_terms = INF_WEIGHT;
        end else begin
            sum = {32'd0, base_term} + {32'd0, dyn_term};
            add_weight_terms = (sum[63:32] != 32'd0) ? INF_WEIGHT : sum[31:0];
        end
    end
    endfunction

    wire [15:0] cfg_qber     = cfg_wdata_i[63:48];
    wire [15:0] cfg_arrival  = cfg_wdata_i[47:32];
    wire [15:0] cfg_fidelity = cfg_wdata_i[31:16];
    wire [15:0] cfg_key      = cfg_wdata_i[15:0];
    wire [31:0] cfg_base     = compute_base(cfg_key, cfg_arrival, cfg_qber, alpha1_q8_8_i, alpha3_q8_8_i, alpha4_q8_8_i);
    wire [31:0] cfg_dyn_term = compute_fidelity_term(cfg_fidelity, alpha2_q8_8_i);
    wire [31:0] cfg_weight   = add_weight_terms(cfg_base, cfg_dyn_term);

    wire [15:0] fidelity_wdata = a_use_cfg ? cfg_fidelity : fdpe_s4_new_fidelity;
    wire [31:0] weight_wdata   = a_use_cfg ? cfg_weight   : fdpe_s4_new_weight;

    always @(posedge clk) begin
        if (a_use_cfg) qber_mem[cfg_addr_i] <= cfg_qber;
        if (a_use_fdpe_read) a_qber_dout <= qber_mem[fdpe_addr_i];
        if (ga_rd_en_i) b_qber_dout <= qber_mem[ga_rd_addr_i];
    end
    always @(posedge clk) begin
        if (a_use_cfg) arrival_mem[cfg_addr_i] <= cfg_arrival;
        if (a_use_fdpe_read) a_arrival_dout <= arrival_mem[fdpe_addr_i];
        if (ga_rd_en_i) b_arrival_dout <= arrival_mem[ga_rd_addr_i];
    end
    always @(posedge clk) begin
        if (a_use_cfg) key_mem[cfg_addr_i] <= cfg_key;
        if (a_use_fdpe_read) a_key_dout <= key_mem[fdpe_addr_i];
        if (ga_rd_en_i) b_key_dout <= key_mem[ga_rd_addr_i];
    end

`ifndef SYNTHESIS
    always @(posedge clk) begin
        if (mem_we) fidelity_mem[mem_waddr] <= fidelity_wdata;
        if (ga_rd_en_i) b_fidelity_dout <= fidelity_mem[ga_rd_addr_i];
    end
    always @(posedge clk) begin
        if (mem_we) weight_mem[mem_waddr] <= weight_wdata;
        if (ga_rd_en_i) b_weight_dout <= weight_mem[ga_rd_addr_i];
    end
    always @(posedge clk) begin
        if (cfg_we_i) base_mem[cfg_addr_i] <= cfg_base;
        base_dout <= base_mem[fdpe_addr_i];
    end
`else
    wire [15:0] fidelity_xpm_doutb;
    wire [31:0] weight_xpm_doutb;
    wire [31:0] base_xpm_doutb;

    xpm_memory_tdpram #(
        .ADDR_WIDTH_A(ADDR_W), .ADDR_WIDTH_B(ADDR_W), .AUTO_SLEEP_TIME(0),
        .BYTE_WRITE_WIDTH_A(16), .BYTE_WRITE_WIDTH_B(16), .CASCADE_HEIGHT(0),
        .CLOCKING_MODE("common_clock"), .ECC_MODE("no_ecc"),
        .MEMORY_INIT_FILE("none"), .MEMORY_INIT_PARAM("0"), .MEMORY_OPTIMIZATION("true"),
        .MEMORY_PRIMITIVE("block"), .MEMORY_SIZE(DEPTH * 16), .MESSAGE_CONTROL(0),
        .READ_DATA_WIDTH_A(16), .READ_DATA_WIDTH_B(16), .READ_LATENCY_A(1), .READ_LATENCY_B(1),
        .READ_RESET_VALUE_A("0"), .READ_RESET_VALUE_B("0"), .USE_EMBEDDED_CONSTRAINT(0),
        .USE_MEM_INIT(0), .WAKEUP_TIME("disable_sleep"), .WRITE_DATA_WIDTH_A(16), .WRITE_DATA_WIDTH_B(16),
        .WRITE_MODE_A("read_first"), .WRITE_MODE_B("read_first")
    ) fidelity_mem_xpm (
        .dbiterra(), .dbiterrb(), .douta(), .doutb(fidelity_xpm_doutb), .sbiterra(), .sbiterrb(),
        .addra(mem_waddr), .addrb(ga_rd_addr_i), .clka(clk), .clkb(clk),
        .dina(fidelity_wdata), .dinb(16'd0), .ena(1'b1), .enb(ga_rd_en_i),
        .injectdbiterra(1'b0), .injectdbiterrb(1'b0), .injectsbiterra(1'b0), .injectsbiterrb(1'b0),
        .regcea(1'b1), .regceb(1'b1), .rsta(~rst_n), .rstb(~rst_n), .sleep(1'b0),
        .wea(mem_we), .web(1'b0)
    );

    xpm_memory_tdpram #(
        .ADDR_WIDTH_A(ADDR_W), .ADDR_WIDTH_B(ADDR_W), .AUTO_SLEEP_TIME(0),
        .BYTE_WRITE_WIDTH_A(32), .BYTE_WRITE_WIDTH_B(32), .CASCADE_HEIGHT(0),
        .CLOCKING_MODE("common_clock"), .ECC_MODE("no_ecc"),
        .MEMORY_INIT_FILE("none"), .MEMORY_INIT_PARAM("0"), .MEMORY_OPTIMIZATION("true"),
        .MEMORY_PRIMITIVE("block"), .MEMORY_SIZE(DEPTH * 32), .MESSAGE_CONTROL(0),
        .READ_DATA_WIDTH_A(32), .READ_DATA_WIDTH_B(32), .READ_LATENCY_A(1), .READ_LATENCY_B(1),
        .READ_RESET_VALUE_A("0"), .READ_RESET_VALUE_B("0"), .USE_EMBEDDED_CONSTRAINT(0),
        .USE_MEM_INIT(0), .WAKEUP_TIME("disable_sleep"), .WRITE_DATA_WIDTH_A(32), .WRITE_DATA_WIDTH_B(32),
        .WRITE_MODE_A("read_first"), .WRITE_MODE_B("read_first")
    ) weight_mem_xpm (
        .dbiterra(), .dbiterrb(), .douta(), .doutb(weight_xpm_doutb), .sbiterra(), .sbiterrb(),
        .addra(mem_waddr), .addrb(ga_rd_addr_i), .clka(clk), .clkb(clk),
        .dina(weight_wdata), .dinb(32'd0), .ena(1'b1), .enb(ga_rd_en_i),
        .injectdbiterra(1'b0), .injectdbiterrb(1'b0), .injectsbiterra(1'b0), .injectsbiterrb(1'b0),
        .regcea(1'b1), .regceb(1'b1), .rsta(~rst_n), .rstb(~rst_n), .sleep(1'b0),
        .wea(mem_we), .web(1'b0)
    );

    xpm_memory_tdpram #(
        .ADDR_WIDTH_A(ADDR_W), .ADDR_WIDTH_B(ADDR_W), .AUTO_SLEEP_TIME(0),
        .BYTE_WRITE_WIDTH_A(32), .BYTE_WRITE_WIDTH_B(32), .CASCADE_HEIGHT(0),
        .CLOCKING_MODE("common_clock"), .ECC_MODE("no_ecc"),
        .MEMORY_INIT_FILE("none"), .MEMORY_INIT_PARAM("0"), .MEMORY_OPTIMIZATION("true"),
        .MEMORY_PRIMITIVE("block"), .MEMORY_SIZE(DEPTH * 32), .MESSAGE_CONTROL(0),
        .READ_DATA_WIDTH_A(32), .READ_DATA_WIDTH_B(32), .READ_LATENCY_A(1), .READ_LATENCY_B(1),
        .READ_RESET_VALUE_A("0"), .READ_RESET_VALUE_B("0"), .USE_EMBEDDED_CONSTRAINT(0),
        .USE_MEM_INIT(0), .WAKEUP_TIME("disable_sleep"), .WRITE_DATA_WIDTH_A(32), .WRITE_DATA_WIDTH_B(32),
        .WRITE_MODE_A("read_first"), .WRITE_MODE_B("read_first")
    ) base_mem_xpm (
        .dbiterra(), .dbiterrb(), .douta(), .doutb(base_xpm_doutb), .sbiterra(), .sbiterrb(),
        .addra(cfg_addr_i), .addrb(fdpe_addr_i), .clka(clk), .clkb(clk),
        .dina(cfg_base), .dinb(32'd0), .ena(cfg_we_i), .enb(a_use_fdpe_read),
        .injectdbiterra(1'b0), .injectdbiterrb(1'b0), .injectsbiterra(1'b0), .injectsbiterrb(1'b0),
        .regcea(1'b1), .regceb(1'b1), .rsta(~rst_n), .rstb(~rst_n), .sleep(1'b0),
        .wea(cfg_we_i), .web(1'b0)
    );

    always @(posedge clk) begin
        if (ga_rd_en_i) begin
            b_fidelity_dout <= fidelity_xpm_doutb;
            b_weight_dout   <= weight_xpm_doutb;
        end
        base_dout <= base_xpm_doutb;
    end
`endif

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fdpe_req_valid <= 1'b0; fdpe_req_addr <= {ADDR_W{1'b0}}; fdpe_req_fidelity <= 16'd0;
            fdpe_s0_valid <= 1'b0; fdpe_s0_addr <= {ADDR_W{1'b0}}; fdpe_s0_fidelity <= 16'd0; fdpe_s0_base <= INF_WEIGHT;
            fdpe_s1_valid <= 1'b0; fdpe_s1_addr <= {ADDR_W{1'b0}}; fdpe_s1_new_fidelity <= 16'd0; fdpe_s1_base <= INF_WEIGHT; fdpe_s1_dyn_term <= INF_WEIGHT;
            fdpe_s2_valid <= 1'b0; fdpe_s2_addr <= {ADDR_W{1'b0}}; fdpe_s2_new_fidelity <= 16'd0; fdpe_s2_new_weight <= INF_WEIGHT;
            fdpe_s3_valid <= 1'b0; fdpe_s3_addr <= {ADDR_W{1'b0}}; fdpe_s3_new_fidelity <= 16'd0; fdpe_s3_new_weight <= INF_WEIGHT;
            fdpe_s4_valid <= 1'b0; fdpe_s4_addr <= {ADDR_W{1'b0}}; fdpe_s4_new_fidelity <= 16'd0; fdpe_s4_new_weight <= INF_WEIGHT;
            ga_pending <= 1'b0; ga_conflict_pending <= 1'b0;
            ga_rd_edge_o <= 64'd0; ga_rd_weight_o <= INF_WEIGHT; ga_rd_valid_o <= 1'b0;
            fdpe_done_o <= 1'b0; fdpe_weight_o <= INF_WEIGHT;
        end else begin
            fdpe_done_o <= 1'b0;
            ga_rd_valid_o <= 1'b0;

            if (ga_pending) begin
                if (ga_conflict_pending) begin
                    ga_rd_valid_o  <= 1'b0;
                    ga_rd_edge_o   <= 64'd0;
                    ga_rd_weight_o <= INF_WEIGHT;
                end else begin
                    ga_rd_valid_o  <= 1'b1;
                    ga_rd_edge_o   <= {b_qber_dout, b_arrival_dout, b_fidelity_dout, b_key_dout};
                    ga_rd_weight_o <= b_weight_dout;
                end
            end

            if (a_use_fdpe_write) begin
                fdpe_done_o   <= 1'b1;
                fdpe_weight_o <= fdpe_s4_new_weight;
            end

            fdpe_s4_valid        <= fdpe_s3_valid;
            fdpe_s4_addr         <= fdpe_s3_addr;
            fdpe_s4_new_fidelity <= fdpe_s3_new_fidelity;
            fdpe_s4_new_weight   <= fdpe_s3_new_weight;

            fdpe_s3_valid        <= fdpe_s2_valid;
            fdpe_s3_addr         <= fdpe_s2_addr;
            fdpe_s3_new_fidelity <= fdpe_s2_new_fidelity;
            fdpe_s3_new_weight   <= fdpe_s2_new_weight;

            if (fdpe_s1_valid) begin
                fdpe_s2_valid        <= 1'b1;
                fdpe_s2_addr         <= fdpe_s1_addr;
                fdpe_s2_new_fidelity <= fdpe_s1_new_fidelity;
                fdpe_s2_new_weight   <= add_weight_terms(fdpe_s1_base, fdpe_s1_dyn_term);
            end else begin
                fdpe_s2_valid        <= 1'b0;
                fdpe_s2_addr         <= {ADDR_W{1'b0}};
                fdpe_s2_new_fidelity <= 16'd0;
                fdpe_s2_new_weight   <= INF_WEIGHT;
            end

            if (fdpe_s0_valid) begin
                fdpe_s1_valid        <= 1'b1;
                fdpe_s1_addr         <= fdpe_s0_addr;
                fdpe_s1_new_fidelity <= fdpe_s0_fidelity;
                fdpe_s1_base         <= fdpe_s0_base;
                fdpe_s1_dyn_term     <= compute_fidelity_term(fdpe_s0_fidelity, alpha2_q8_8_i);
            end else begin
                fdpe_s1_valid        <= 1'b0;
                fdpe_s1_addr         <= {ADDR_W{1'b0}};
                fdpe_s1_new_fidelity <= 16'd0;
                fdpe_s1_base         <= INF_WEIGHT;
                fdpe_s1_dyn_term     <= INF_WEIGHT;
            end

            if (fdpe_req_valid) begin
                fdpe_s0_valid    <= 1'b1;
                fdpe_s0_addr     <= fdpe_req_addr;
                fdpe_s0_fidelity <= fdpe_req_fidelity;
                fdpe_s0_base     <= base_dout;
            end else begin
                fdpe_s0_valid    <= 1'b0;
                fdpe_s0_addr     <= {ADDR_W{1'b0}};
                fdpe_s0_fidelity <= 16'd0;
                fdpe_s0_base     <= INF_WEIGHT;
            end

            if (a_use_fdpe_read) begin
                fdpe_req_valid    <= 1'b1;
                fdpe_req_addr     <= fdpe_addr_i;
                fdpe_req_fidelity <= fdpe_fidelity_i;
            end else begin
                fdpe_req_valid    <= 1'b0;
                fdpe_req_addr     <= {ADDR_W{1'b0}};
                fdpe_req_fidelity <= 16'd0;
            end

            ga_pending <= ga_rd_en_i;
            ga_conflict_pending <= ga_rd_en_i && (
                (a_use_fdpe_read && (ga_rd_addr_i == fdpe_addr_i)) ||
                (fdpe_req_valid && (ga_rd_addr_i == fdpe_req_addr)) ||
                (fdpe_s0_valid && (ga_rd_addr_i == fdpe_s0_addr)) ||
                (fdpe_s1_valid && (ga_rd_addr_i == fdpe_s1_addr)) ||
                (fdpe_s2_valid && (ga_rd_addr_i == fdpe_s2_addr)) ||
                (fdpe_s3_valid && (ga_rd_addr_i == fdpe_s3_addr)) ||
                (fdpe_s4_valid && (ga_rd_addr_i == fdpe_s4_addr))
            );
        end
    end
endmodule
