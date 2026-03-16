`timescale 1ns/1ps

module skag_mem_tc4 #(
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
    localparam integer DIV_W = 40;

    (* ram_style = "block" *) reg [15:0] qber_mem    [0:DEPTH-1];
    (* ram_style = "block" *) reg [15:0] arrival_mem [0:DEPTH-1];
    (* ram_style = "block" *) reg [15:0] key_mem     [0:DEPTH-1];
`ifndef SYNTHESIS
    (* ram_style = "block" *) reg [15:0] fidelity_mem [0:DEPTH-1];
    (* ram_style = "block" *) reg [31:0] weight_mem   [0:DEPTH-1];
    (* ram_style = "block" *) reg [31:0] base_mem     [0:DEPTH-1];
`endif

    reg [15:0] b_qber_dout, b_arrival_dout, b_key_dout;
    reg [15:0] b_fidelity_dout;
    reg [31:0] b_weight_dout;
    reg [31:0] base_dout;

    reg                  fdpe_req0_valid;
    reg [ADDR_W-1:0]     fdpe_req0_addr;
    reg [15:0]           fdpe_req0_fidelity;

    reg                  fdpe_req1_valid;
    reg [ADDR_W-1:0]     fdpe_req1_addr;
    reg [15:0]           fdpe_req1_fidelity;

    reg                  fdpe_req2_valid;
    reg [ADDR_W-1:0]     fdpe_req2_addr;
    reg [15:0]           fdpe_req2_fidelity;
    reg [31:0]           fdpe_req2_base;

    reg                  div_active;
    reg [ADDR_W-1:0]     div_addr;
    reg [15:0]           div_fidelity;
    reg [31:0]           div_base;
    reg [DIV_W-1:0]      div_quot;
    reg [16:0]           div_rem;
    reg [15:0]           div_den;
    reg [5:0]            div_count;

    reg                  fdpe_add_valid;
    reg [ADDR_W-1:0]     fdpe_add_addr;
    reg [15:0]           fdpe_add_fidelity;
    reg [31:0]           fdpe_add_base;
    reg [31:0]           fdpe_add_dyn_term;

    reg                  fdpe_commit_valid;
    reg [ADDR_W-1:0]     fdpe_commit_addr;
    reg [15:0]           fdpe_commit_fidelity;
    reg [31:0]           fdpe_commit_weight;

    reg                  ga_pending;
    reg                  ga_conflict_pending;

    reg [DIV_W-1:0]      div_quot_next;
    reg [16:0]           div_rem_next;
    reg [16:0]           div_trial_rem;
    reg                  div_bit_next;
    reg [31:0]           div_result_final;
    reg [63:0]           add_sum;

    wire fdpe_busy = fdpe_req0_valid || fdpe_req1_valid || fdpe_req2_valid || div_active || fdpe_add_valid || fdpe_commit_valid;
    wire a_use_fdpe_write = fdpe_commit_valid;
    wire a_use_fdpe_read  = (!fdpe_busy) && fdpe_upd_valid_i;
    wire a_use_cfg        = (!a_use_fdpe_write) && (!a_use_fdpe_read) && cfg_we_i;
    wire [ADDR_W-1:0] mem_waddr = a_use_cfg ? cfg_addr_i : fdpe_commit_addr;
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

    wire [15:0] fidelity_wdata = a_use_cfg ? cfg_fidelity : fdpe_commit_fidelity;
    wire [31:0] weight_wdata   = a_use_cfg ? cfg_weight   : fdpe_commit_weight;

    always @(posedge clk) begin
        if (a_use_cfg) qber_mem[cfg_addr_i] <= cfg_qber;
        if (ga_rd_en_i) b_qber_dout <= qber_mem[ga_rd_addr_i];
    end
    always @(posedge clk) begin
        if (a_use_cfg) arrival_mem[cfg_addr_i] <= cfg_arrival;
        if (ga_rd_en_i) b_arrival_dout <= arrival_mem[ga_rd_addr_i];
    end
    always @(posedge clk) begin
        if (a_use_cfg) key_mem[cfg_addr_i] <= cfg_key;
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
        .READ_DATA_WIDTH_A(16), .READ_DATA_WIDTH_B(16), .READ_LATENCY_A(2), .READ_LATENCY_B(2),
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
        .READ_DATA_WIDTH_A(32), .READ_DATA_WIDTH_B(32), .READ_LATENCY_A(2), .READ_LATENCY_B(2),
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
        .READ_DATA_WIDTH_A(32), .READ_DATA_WIDTH_B(32), .READ_LATENCY_A(2), .READ_LATENCY_B(2),
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
            fdpe_req0_valid <= 1'b0; fdpe_req0_addr <= {ADDR_W{1'b0}}; fdpe_req0_fidelity <= 16'd0;
            fdpe_req1_valid <= 1'b0; fdpe_req1_addr <= {ADDR_W{1'b0}}; fdpe_req1_fidelity <= 16'd0;
            fdpe_req2_valid <= 1'b0; fdpe_req2_addr <= {ADDR_W{1'b0}}; fdpe_req2_fidelity <= 16'd0; fdpe_req2_base <= INF_WEIGHT;
            div_active <= 1'b0; div_addr <= {ADDR_W{1'b0}}; div_fidelity <= 16'd0; div_base <= INF_WEIGHT;
            div_quot <= {DIV_W{1'b0}}; div_rem <= 17'd0; div_den <= 16'd0; div_count <= 6'd0;
            fdpe_add_valid <= 1'b0; fdpe_add_addr <= {ADDR_W{1'b0}}; fdpe_add_fidelity <= 16'd0; fdpe_add_base <= INF_WEIGHT; fdpe_add_dyn_term <= INF_WEIGHT;
            fdpe_commit_valid <= 1'b0; fdpe_commit_addr <= {ADDR_W{1'b0}}; fdpe_commit_fidelity <= 16'd0; fdpe_commit_weight <= INF_WEIGHT;
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
                fdpe_weight_o <= fdpe_commit_weight;
            end

            if (fdpe_add_valid) begin
                fdpe_commit_valid    <= 1'b1;
                fdpe_commit_addr     <= fdpe_add_addr;
                fdpe_commit_fidelity <= fdpe_add_fidelity;
                fdpe_commit_weight   <= add_weight_terms(fdpe_add_base, fdpe_add_dyn_term);
            end else begin
                fdpe_commit_valid    <= 1'b0;
                fdpe_commit_addr     <= {ADDR_W{1'b0}};
                fdpe_commit_fidelity <= 16'd0;
                fdpe_commit_weight   <= INF_WEIGHT;
            end
            fdpe_add_valid <= 1'b0;

            if (div_active) begin
                div_trial_rem = {div_rem[15:0], div_quot[DIV_W-1]};
                if (div_trial_rem >= {1'b0, div_den}) begin
                    div_rem_next  = div_trial_rem - {1'b0, div_den};
                    div_bit_next  = 1'b1;
                end else begin
                    div_rem_next  = div_trial_rem;
                    div_bit_next  = 1'b0;
                end
                div_quot_next = {div_quot[DIV_W-2:0], div_bit_next};

                if (div_count == 6'd1) begin
                    div_active <= 1'b0;
                    div_quot   <= div_quot_next;
                    div_rem    <= div_rem_next;
                    div_count  <= 6'd0;

                    if (div_quot_next[DIV_W-1:32] != { (DIV_W-32){1'b0} }) begin
                        div_result_final = INF_WEIGHT;
                    end else begin
                        div_result_final = div_quot_next[31:0];
                    end

                    fdpe_add_valid    <= 1'b1;
                    fdpe_add_addr     <= div_addr;
                    fdpe_add_fidelity <= div_fidelity;
                    fdpe_add_base     <= div_base;
                    fdpe_add_dyn_term <= div_result_final;
                end else begin
                    div_quot  <= div_quot_next;
                    div_rem   <= div_rem_next;
                    div_count <= div_count - 6'd1;
                end
            end

            if (fdpe_req2_valid) begin
                if ((fdpe_req2_fidelity == 16'd0) || (fdpe_req2_base == INF_WEIGHT)) begin
                    fdpe_add_valid    <= 1'b1;
                    fdpe_add_addr     <= fdpe_req2_addr;
                    fdpe_add_fidelity <= fdpe_req2_fidelity;
                    fdpe_add_base     <= fdpe_req2_base;
                    fdpe_add_dyn_term <= INF_WEIGHT;
                end else begin
                    div_active   <= 1'b1;
                    div_addr     <= fdpe_req2_addr;
                    div_fidelity <= fdpe_req2_fidelity;
                    div_base     <= fdpe_req2_base;
                    div_quot     <= {24'd0, alpha2_q8_8_i} << 24;
                    div_rem      <= 17'd0;
                    div_den      <= fdpe_req2_fidelity;
                    div_count    <= 6'd40;
                end
            end

            fdpe_req2_valid    <= fdpe_req1_valid;
            fdpe_req2_addr     <= fdpe_req1_addr;
            fdpe_req2_fidelity <= fdpe_req1_fidelity;
            fdpe_req2_base     <= base_dout;

            fdpe_req1_valid    <= fdpe_req0_valid;
            fdpe_req1_addr     <= fdpe_req0_addr;
            fdpe_req1_fidelity <= fdpe_req0_fidelity;

            if (a_use_fdpe_read) begin
                fdpe_req0_valid    <= 1'b1;
                fdpe_req0_addr     <= fdpe_addr_i;
                fdpe_req0_fidelity <= fdpe_fidelity_i;
            end else begin
                fdpe_req0_valid    <= 1'b0;
                fdpe_req0_addr     <= {ADDR_W{1'b0}};
                fdpe_req0_fidelity <= 16'd0;
            end

            ga_pending <= ga_rd_en_i;
            ga_conflict_pending <= ga_rd_en_i && (
                (a_use_fdpe_read && (ga_rd_addr_i == fdpe_addr_i)) ||
                (fdpe_req0_valid && (ga_rd_addr_i == fdpe_req0_addr)) ||
                (fdpe_req1_valid && (ga_rd_addr_i == fdpe_req1_addr)) ||
                (fdpe_req2_valid && (ga_rd_addr_i == fdpe_req2_addr)) ||
                (div_active && (ga_rd_addr_i == div_addr)) ||
                (fdpe_add_valid && (ga_rd_addr_i == fdpe_add_addr)) ||
                (fdpe_commit_valid && (ga_rd_addr_i == fdpe_commit_addr))
            );
        end
    end
endmodule
