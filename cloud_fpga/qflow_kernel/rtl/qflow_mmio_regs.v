`timescale 1ns/1ps
// -----------------------------------------------------------------------------
// QFlow AWS F2 starter kernel - local MMIO/register wrapper
// -----------------------------------------------------------------------------
// This module is NOT an AWS Shell/CL replacement. It is a small local wrapper
// that gives qflow_cloud_kernel a host-style register interface before paid AWS
// debugging. The same register map can later be connected to the AWS CL AXI-Lite
// or OCL/MMIO fabric.
//
// Register policy:
//   - Writes are synchronous on wr_en.
//   - Reads are combinational from addr.
//   - Writing CONTROL.start creates a one-cycle kernel start pulse.
//   - STATUS.done is sticky until the next start or soft reset.
//   - Kernel outputs are latched on the kernel done pulse.

module qflow_mmio_regs #(
    parameter NUM_EDGES      = 8,
    parameter NUM_CAND       = 4,
    parameter MAX_PATH_EDGES = 4,
    parameter EDGE_ID_W      = 4,
    parameter FID_W          = 16,
    parameter SCORE_W        = 32
)(
    input  wire        clk,
    input  wire        rst_n,
    input  wire        wr_en,
    input  wire        rd_en,
    input  wire [11:0] addr,
    input  wire [31:0] wdata,
    output reg  [31:0] rdata,

    output wire        kernel_done_pulse,
    output wire        status_done,
    output wire        status_valid_path,
    output wire        status_no_path,
    output wire        status_busy
);
    localparam [11:0] REG_CONTROL      = 12'h000;
    localparam [11:0] REG_STATUS       = 12'h004;
    localparam [11:0] REG_SRC_NODE     = 12'h010;
    localparam [11:0] REG_DST_NODE     = 12'h014;
    localparam [11:0] REG_TIME_NOW     = 12'h018;
    localparam [11:0] REG_F_MIN        = 12'h01C;

    localparam [11:0] EDGE_BASE        = 12'h100;
    localparam [11:0] EDGE_STRIDE      = 12'h020;
    localparam [11:0] EDGE_KEY_COUNT   = 12'h000;
    localparam [11:0] EDGE_F_INIT      = 12'h004;
    localparam [11:0] EDGE_DECAY_IDX   = 12'h008;
    localparam [11:0] EDGE_ARRIVAL     = 12'h00C;
    localparam [11:0] EDGE_QBER        = 12'h010;
    localparam [11:0] EDGE_DISTANCE    = 12'h014;

    localparam [11:0] CAND_BASE        = 12'h300;
    localparam [11:0] CAND_STRIDE      = 12'h010;
    localparam [11:0] CAND_EDGES       = 12'h000;
    localparam [11:0] CAND_LEN         = 12'h004;

    localparam [11:0] REG_SELECTED_ID  = 12'h400;
    localparam [11:0] REG_BEST_WEIGHT  = 12'h404;
    localparam [11:0] REG_BOTTLENECK   = 12'h408;
    localparam [11:0] REG_LATENCY      = 12'h40C;

    reg [5:0]  src_node_r;
    reg [5:0]  dst_node_r;
    reg [31:0] time_now_r;
    reg [FID_W-1:0] f_min_threshold_r;

    reg [NUM_EDGES*16-1:0]      key_counts_flat_r;
    reg [NUM_EDGES*FID_W-1:0]   f_init_flat_r;
    reg [NUM_EDGES*8-1:0]       decay_idx_flat_r;
    reg [NUM_EDGES*16-1:0]      arrival_rate_flat_r;
    reg [NUM_EDGES*FID_W-1:0]   qber_flat_r;
    reg [NUM_EDGES*SCORE_W-1:0] distance_cost_flat_r;

    reg [NUM_CAND*MAX_PATH_EDGES*EDGE_ID_W-1:0] cand_edges_flat_r;
    reg [NUM_CAND*3-1:0] cand_lens_flat_r;

    reg start_pulse_r;
    reg busy_r;
    reg done_sticky_r;
    reg valid_path_r;
    reg no_path_r;
    reg [1:0] selected_path_id_r;
    reg [SCORE_W-1:0] best_weight_r;
    reg [FID_W-1:0] bottleneck_fidelity_r;
    reg [31:0] latency_cycles_r;

    wire soft_reset_req;
    assign soft_reset_req = wr_en && (addr == REG_CONTROL) && wdata[1];

    wire kernel_done;
    wire kernel_valid_path;
    wire kernel_no_path;
    wire [1:0] kernel_selected_path_id;
    wire [SCORE_W-1:0] kernel_best_weight;
    wire [FID_W-1:0] kernel_bottleneck_fidelity;
    wire [31:0] kernel_latency_cycles;

    assign kernel_done_pulse = kernel_done;
    assign status_done       = done_sticky_r;
    assign status_valid_path = valid_path_r;
    assign status_no_path    = no_path_r;
    assign status_busy       = busy_r;

    qflow_cloud_kernel #(
        .NUM_EDGES(NUM_EDGES),
        .NUM_CAND(NUM_CAND),
        .MAX_PATH_EDGES(MAX_PATH_EDGES),
        .EDGE_ID_W(EDGE_ID_W),
        .FID_W(FID_W),
        .SCORE_W(SCORE_W)
    ) u_kernel (
        .clk(clk),
        .rst_n(rst_n && !soft_reset_req),
        .start(start_pulse_r),
        .src_node(src_node_r),
        .dst_node(dst_node_r),
        .time_now(time_now_r),
        .f_min_threshold(f_min_threshold_r),
        .key_counts_flat(key_counts_flat_r),
        .f_init_flat(f_init_flat_r),
        .decay_idx_flat(decay_idx_flat_r),
        .arrival_rate_flat(arrival_rate_flat_r),
        .qber_flat(qber_flat_r),
        .distance_cost_flat(distance_cost_flat_r),
        .cand_edges_flat(cand_edges_flat_r),
        .cand_lens_flat(cand_lens_flat_r),
        .done(kernel_done),
        .valid_path(kernel_valid_path),
        .no_path(kernel_no_path),
        .selected_path_id(kernel_selected_path_id),
        .best_weight(kernel_best_weight),
        .bottleneck_fidelity(kernel_bottleneck_fidelity),
        .latency_cycles(kernel_latency_cycles)
    );

    integer edge_wr_idx;
    integer cand_wr_idx;
    reg [11:0] edge_wr_off;
    reg [11:0] cand_wr_off;

    always @(posedge clk) begin
        if (!rst_n) begin
            src_node_r              <= 6'd0;
            dst_node_r              <= 6'd0;
            time_now_r              <= 32'd0;
            f_min_threshold_r       <= {FID_W{1'b0}};
            key_counts_flat_r       <= {(NUM_EDGES*16){1'b0}};
            f_init_flat_r           <= {(NUM_EDGES*FID_W){1'b0}};
            decay_idx_flat_r        <= {(NUM_EDGES*8){1'b0}};
            arrival_rate_flat_r     <= {(NUM_EDGES*16){1'b0}};
            qber_flat_r             <= {(NUM_EDGES*FID_W){1'b0}};
            distance_cost_flat_r    <= {(NUM_EDGES*SCORE_W){1'b0}};
            cand_edges_flat_r       <= {(NUM_CAND*MAX_PATH_EDGES*EDGE_ID_W){1'b0}};
            cand_lens_flat_r        <= {(NUM_CAND*3){1'b0}};
            start_pulse_r           <= 1'b0;
            busy_r                  <= 1'b0;
            done_sticky_r           <= 1'b0;
            valid_path_r            <= 1'b0;
            no_path_r               <= 1'b0;
            selected_path_id_r      <= 2'd0;
            best_weight_r           <= {SCORE_W{1'b0}};
            bottleneck_fidelity_r   <= {FID_W{1'b0}};
            latency_cycles_r        <= 32'd0;
        end else begin
            start_pulse_r <= 1'b0;

            if (soft_reset_req) begin
                busy_r                  <= 1'b0;
                done_sticky_r           <= 1'b0;
                valid_path_r            <= 1'b0;
                no_path_r               <= 1'b0;
                selected_path_id_r      <= 2'd0;
                best_weight_r           <= {SCORE_W{1'b0}};
                bottleneck_fidelity_r   <= {FID_W{1'b0}};
                latency_cycles_r        <= 32'd0;
            end else begin
                if (wr_en) begin
                    case (addr)
                        REG_CONTROL: begin
                            if (wdata[0]) begin
                                start_pulse_r <= 1'b1;
                                busy_r        <= 1'b1;
                                done_sticky_r <= 1'b0;
                                valid_path_r  <= 1'b0;
                                no_path_r     <= 1'b0;
                            end
                        end
                        REG_SRC_NODE: src_node_r <= wdata[5:0];
                        REG_DST_NODE: dst_node_r <= wdata[5:0];
                        REG_TIME_NOW: time_now_r <= wdata;
                        REG_F_MIN:    f_min_threshold_r <= wdata[FID_W-1:0];
                        default: begin
                            if ((addr >= EDGE_BASE) && (addr < (EDGE_BASE + NUM_EDGES*EDGE_STRIDE))) begin
                                edge_wr_idx = (addr - EDGE_BASE) >> 5;
                                edge_wr_off = (addr - EDGE_BASE) & 12'h01F;
                                case (edge_wr_off)
                                    EDGE_KEY_COUNT: key_counts_flat_r[edge_wr_idx*16 +: 16] <= wdata[15:0];
                                    EDGE_F_INIT:    f_init_flat_r[edge_wr_idx*FID_W +: FID_W] <= wdata[FID_W-1:0];
                                    EDGE_DECAY_IDX: decay_idx_flat_r[edge_wr_idx*8 +: 8] <= wdata[7:0];
                                    EDGE_ARRIVAL:   arrival_rate_flat_r[edge_wr_idx*16 +: 16] <= wdata[15:0];
                                    EDGE_QBER:      qber_flat_r[edge_wr_idx*FID_W +: FID_W] <= wdata[FID_W-1:0];
                                    EDGE_DISTANCE:  distance_cost_flat_r[edge_wr_idx*SCORE_W +: SCORE_W] <= wdata[SCORE_W-1:0];
                                    default: begin end
                                endcase
                            end else if ((addr >= CAND_BASE) && (addr < (CAND_BASE + NUM_CAND*CAND_STRIDE))) begin
                                cand_wr_idx = (addr - CAND_BASE) >> 4;
                                cand_wr_off = (addr - CAND_BASE) & 12'h00F;
                                case (cand_wr_off)
                                    CAND_EDGES: cand_edges_flat_r[cand_wr_idx*MAX_PATH_EDGES*EDGE_ID_W +: MAX_PATH_EDGES*EDGE_ID_W] <= wdata[MAX_PATH_EDGES*EDGE_ID_W-1:0];
                                    CAND_LEN:   cand_lens_flat_r[cand_wr_idx*3 +: 3] <= wdata[2:0];
                                    default: begin end
                                endcase
                            end
                        end
                    endcase
                end

                if (kernel_done) begin
                    busy_r                <= 1'b0;
                    done_sticky_r         <= 1'b1;
                    valid_path_r          <= kernel_valid_path;
                    no_path_r             <= kernel_no_path;
                    selected_path_id_r    <= kernel_selected_path_id;
                    best_weight_r         <= kernel_best_weight;
                    bottleneck_fidelity_r <= kernel_bottleneck_fidelity;
                    latency_cycles_r      <= kernel_latency_cycles;
                end
            end
        end
    end

    integer edge_rd_idx;
    integer cand_rd_idx;
    reg [11:0] edge_rd_off;
    reg [11:0] cand_rd_off;

    always @* begin
        rdata = 32'd0;
        if (rd_en) begin
            case (addr)
                REG_CONTROL:     rdata = 32'd0;
                REG_STATUS:      rdata = {28'd0, busy_r, no_path_r, valid_path_r, done_sticky_r};
                REG_SRC_NODE:    rdata = {26'd0, src_node_r};
                REG_DST_NODE:    rdata = {26'd0, dst_node_r};
                REG_TIME_NOW:    rdata = time_now_r;
                REG_F_MIN:       rdata = {{(32-FID_W){1'b0}}, f_min_threshold_r};
                REG_SELECTED_ID: rdata = {30'd0, selected_path_id_r};
                REG_BEST_WEIGHT: rdata = best_weight_r;
                REG_BOTTLENECK:  rdata = {{(32-FID_W){1'b0}}, bottleneck_fidelity_r};
                REG_LATENCY:     rdata = latency_cycles_r;
                default: begin
                    if ((addr >= EDGE_BASE) && (addr < (EDGE_BASE + NUM_EDGES*EDGE_STRIDE))) begin
                        edge_rd_idx = (addr - EDGE_BASE) >> 5;
                        edge_rd_off = (addr - EDGE_BASE) & 12'h01F;
                        case (edge_rd_off)
                            EDGE_KEY_COUNT: rdata = {16'd0, key_counts_flat_r[edge_rd_idx*16 +: 16]};
                            EDGE_F_INIT:    rdata = {{(32-FID_W){1'b0}}, f_init_flat_r[edge_rd_idx*FID_W +: FID_W]};
                            EDGE_DECAY_IDX: rdata = {24'd0, decay_idx_flat_r[edge_rd_idx*8 +: 8]};
                            EDGE_ARRIVAL:   rdata = {16'd0, arrival_rate_flat_r[edge_rd_idx*16 +: 16]};
                            EDGE_QBER:      rdata = {{(32-FID_W){1'b0}}, qber_flat_r[edge_rd_idx*FID_W +: FID_W]};
                            EDGE_DISTANCE:  rdata = distance_cost_flat_r[edge_rd_idx*SCORE_W +: SCORE_W];
                            default:        rdata = 32'd0;
                        endcase
                    end else if ((addr >= CAND_BASE) && (addr < (CAND_BASE + NUM_CAND*CAND_STRIDE))) begin
                        cand_rd_idx = (addr - CAND_BASE) >> 4;
                        cand_rd_off = (addr - CAND_BASE) & 12'h00F;
                        case (cand_rd_off)
                            CAND_EDGES: rdata = {{(32-(MAX_PATH_EDGES*EDGE_ID_W)){1'b0}}, cand_edges_flat_r[cand_rd_idx*MAX_PATH_EDGES*EDGE_ID_W +: MAX_PATH_EDGES*EDGE_ID_W]};
                            CAND_LEN:   rdata = {29'd0, cand_lens_flat_r[cand_rd_idx*3 +: 3]};
                            default:    rdata = 32'd0;
                        endcase
                    end
                end
            endcase
        end
    end
endmodule
