`timescale 1ns/1ps

module skag_mem_bram #(
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

    // Three raw-field banks inferred as BRAM reasonably well.
    (* ram_style = "block" *) reg [15:0] qber_mem     [0:DEPTH-1];
    (* ram_style = "block" *) reg [15:0] arrival_mem  [0:DEPTH-1];
    (* ram_style = "block" *) reg [15:0] key_mem      [0:DEPTH-1];

`ifndef SYNTHESIS
    // Portable simulation model for fidelity bank.
    (* ram_style = "block" *) reg [15:0] fidelity_mem [0:DEPTH-1];
`endif

    reg [15:0] a_qber_dout;
    reg [15:0] a_arrival_dout;
    reg [15:0] a_key_dout;

    reg [15:0] b_qber_dout;
    reg [15:0] b_arrival_dout;
    reg [15:0] b_fidelity_dout;
    reg [15:0] b_key_dout;

    reg                  fdpe_s0_valid;
    reg [ADDR_W-1:0]     fdpe_s0_addr;
    reg [15:0]           fdpe_s0_fidelity;

    reg                  fdpe_s1_valid;
    reg [ADDR_W-1:0]     fdpe_s1_addr;
    reg [15:0]           fdpe_s1_new_fidelity;
    reg [31:0]           fdpe_s1_new_weight;

    reg                  fdpe_s2_valid;
    reg [ADDR_W-1:0]     fdpe_s2_addr;
    reg [15:0]           fdpe_s2_new_fidelity;
    reg [31:0]           fdpe_s2_new_weight;

    reg                  ga_pending;
    reg                  ga_conflict_pending;

    wire a_use_fdpe_write;
    wire a_use_fdpe_read;
    wire a_use_cfg;

    assign a_use_fdpe_write = fdpe_s2_valid;
    assign a_use_fdpe_read  = (!fdpe_s0_valid) && (!fdpe_s1_valid) && (!fdpe_s2_valid) && fdpe_upd_valid_i;
    assign a_use_cfg        = (!a_use_fdpe_write) && (!a_use_fdpe_read) && cfg_we_i;

    // Single-write-port muxing for the fidelity bank. This is the remaining bank
    // Vivado kept pushing into LUTRAM; synthesis uses an explicit XPM BRAM.
    wire                  fidelity_we;
    wire [ADDR_W-1:0]     fidelity_waddr;
    wire [15:0]           fidelity_wdata;
    assign fidelity_we    = a_use_cfg || a_use_fdpe_write;
    assign fidelity_waddr = a_use_cfg ? cfg_addr_i : fdpe_s2_addr;
    assign fidelity_wdata = a_use_cfg ? cfg_wdata_i[31:16] : fdpe_s2_new_fidelity;

    function [31:0] compute_weight;
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

    always @(posedge clk) begin
        if (a_use_cfg)
            qber_mem[cfg_addr_i] <= cfg_wdata_i[63:48];
        if (a_use_fdpe_read)
            a_qber_dout <= qber_mem[fdpe_addr_i];
        if (ga_rd_en_i)
            b_qber_dout <= qber_mem[ga_rd_addr_i];
    end

    always @(posedge clk) begin
        if (a_use_cfg)
            arrival_mem[cfg_addr_i] <= cfg_wdata_i[47:32];
        if (a_use_fdpe_read)
            a_arrival_dout <= arrival_mem[fdpe_addr_i];
        if (ga_rd_en_i)
            b_arrival_dout <= arrival_mem[ga_rd_addr_i];
    end

`ifndef SYNTHESIS
    always @(posedge clk) begin
        if (fidelity_we)
            fidelity_mem[fidelity_waddr] <= fidelity_wdata;
        if (ga_rd_en_i)
            b_fidelity_dout <= fidelity_mem[ga_rd_addr_i];
    end
`else
    wire [15:0] fidelity_xpm_doutb;
    xpm_memory_tdpram #(
        .ADDR_WIDTH_A(ADDR_W),
        .ADDR_WIDTH_B(ADDR_W),
        .AUTO_SLEEP_TIME(0),
        .BYTE_WRITE_WIDTH_A(16),
        .BYTE_WRITE_WIDTH_B(16),
        .CASCADE_HEIGHT(0),
        .CLOCKING_MODE("common_clock"),
        .ECC_MODE("no_ecc"),
        .MEMORY_INIT_FILE("none"),
        .MEMORY_INIT_PARAM("0"),
        .MEMORY_OPTIMIZATION("true"),
        .MEMORY_PRIMITIVE("block"),
        .MEMORY_SIZE(DEPTH * 16),
        .MESSAGE_CONTROL(0),
        .READ_DATA_WIDTH_A(16),
        .READ_DATA_WIDTH_B(16),
        .READ_LATENCY_A(1),
        .READ_LATENCY_B(1),
        .READ_RESET_VALUE_A("0"),
        .READ_RESET_VALUE_B("0"),
        .USE_EMBEDDED_CONSTRAINT(0),
        .USE_MEM_INIT(0),
        .WAKEUP_TIME("disable_sleep"),
        .WRITE_DATA_WIDTH_A(16),
        .WRITE_DATA_WIDTH_B(16),
        .WRITE_MODE_A("read_first"),
        .WRITE_MODE_B("read_first")
    ) fidelity_mem_xpm (
        .dbiterra(), .dbiterrb(),
        .douta(), .doutb(fidelity_xpm_doutb),
        .sbiterra(), .sbiterrb(),
        .addra(fidelity_waddr),
        .addrb(ga_rd_addr_i),
        .clka(clk), .clkb(clk),
        .dina(fidelity_wdata), .dinb(16'd0),
        .ena(1'b1), .enb(ga_rd_en_i),
        .injectdbiterra(1'b0), .injectdbiterrb(1'b0),
        .injectsbiterra(1'b0), .injectsbiterrb(1'b0),
        .regcea(1'b1), .regceb(1'b1),
        .rsta(~rst_n), .rstb(~rst_n),
        .sleep(1'b0),
        .wea(fidelity_we), .web(1'b0)
    );

    always @(posedge clk) begin
        if (ga_rd_en_i)
            b_fidelity_dout <= fidelity_xpm_doutb;
    end
`endif

    always @(posedge clk) begin
        if (a_use_cfg)
            key_mem[cfg_addr_i] <= cfg_wdata_i[15:0];
        if (a_use_fdpe_read)
            a_key_dout <= key_mem[fdpe_addr_i];
        if (ga_rd_en_i)
            b_key_dout <= key_mem[ga_rd_addr_i];
    end

    reg [63:0] new_edge_v;
    reg [31:0] new_weight_v;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fdpe_s0_valid        <= 1'b0;
            fdpe_s0_addr         <= {ADDR_W{1'b0}};
            fdpe_s0_fidelity     <= 16'd0;
            fdpe_s1_valid        <= 1'b0;
            fdpe_s1_addr         <= {ADDR_W{1'b0}};
            fdpe_s1_new_fidelity <= 16'd0;
            fdpe_s1_new_weight   <= INF_WEIGHT;
            fdpe_s2_valid        <= 1'b0;
            fdpe_s2_addr         <= {ADDR_W{1'b0}};
            fdpe_s2_new_fidelity <= 16'd0;
            fdpe_s2_new_weight   <= INF_WEIGHT;
            ga_pending           <= 1'b0;
            ga_conflict_pending  <= 1'b0;
            ga_rd_edge_o         <= 64'd0;
            ga_rd_weight_o       <= INF_WEIGHT;
            ga_rd_valid_o        <= 1'b0;
            fdpe_done_o          <= 1'b0;
            fdpe_weight_o        <= INF_WEIGHT;
        end else begin
            fdpe_done_o   <= 1'b0;
            ga_rd_valid_o <= 1'b0;

            if (ga_pending) begin
                if (ga_conflict_pending) begin
                    ga_rd_valid_o  <= 1'b0;
                    ga_rd_edge_o   <= 64'd0;
                    ga_rd_weight_o <= INF_WEIGHT;
                end else begin
                    ga_rd_valid_o  <= 1'b1;
                    ga_rd_edge_o   <= {b_qber_dout, b_arrival_dout, b_fidelity_dout, b_key_dout};
                    ga_rd_weight_o <= compute_weight({b_qber_dout, b_arrival_dout, b_fidelity_dout, b_key_dout},
                                                     alpha1_q8_8_i, alpha2_q8_8_i,
                                                     alpha3_q8_8_i, alpha4_q8_8_i);
                end
            end

            if (a_use_fdpe_write) begin
                fdpe_done_o   <= 1'b1;
                fdpe_weight_o <= fdpe_s2_new_weight;
            end

            fdpe_s2_valid        <= fdpe_s1_valid;
            fdpe_s2_addr         <= fdpe_s1_addr;
            fdpe_s2_new_fidelity <= fdpe_s1_new_fidelity;
            fdpe_s2_new_weight   <= fdpe_s1_new_weight;

            if (fdpe_s0_valid) begin
                new_edge_v = {a_qber_dout, a_arrival_dout, fdpe_s0_fidelity, a_key_dout};
                new_weight_v = compute_weight(new_edge_v,
                                              alpha1_q8_8_i, alpha2_q8_8_i,
                                              alpha3_q8_8_i, alpha4_q8_8_i);
                fdpe_s1_valid        <= 1'b1;
                fdpe_s1_addr         <= fdpe_s0_addr;
                fdpe_s1_new_fidelity <= fdpe_s0_fidelity;
                fdpe_s1_new_weight   <= new_weight_v;
            end else begin
                fdpe_s1_valid        <= 1'b0;
                fdpe_s1_addr         <= {ADDR_W{1'b0}};
                fdpe_s1_new_fidelity <= 16'd0;
                fdpe_s1_new_weight   <= INF_WEIGHT;
            end

            if (a_use_fdpe_read) begin
                fdpe_s0_valid    <= 1'b1;
                fdpe_s0_addr     <= fdpe_addr_i;
                fdpe_s0_fidelity <= fdpe_fidelity_i;
            end else begin
                fdpe_s0_valid    <= 1'b0;
                fdpe_s0_addr     <= {ADDR_W{1'b0}};
                fdpe_s0_fidelity <= 16'd0;
            end

            ga_pending <= ga_rd_en_i;
            ga_conflict_pending <= ga_rd_en_i && (
                (a_use_fdpe_read  && (ga_rd_addr_i == fdpe_addr_i))  ||
                (fdpe_s0_valid    && (ga_rd_addr_i == fdpe_s0_addr)) ||
                (fdpe_s1_valid    && (ga_rd_addr_i == fdpe_s1_addr)) ||
                (fdpe_s2_valid    && (ga_rd_addr_i == fdpe_s2_addr))
            );
        end
    end

endmodule
