`timescale 1ns/1ps
// -----------------------------------------------------------------------------
// QFlow AWS F2 starter kernel - local top before AWS Custom Logic integration
// -----------------------------------------------------------------------------
// This wrapper is intentionally small and deterministic:
//   host/testbench inputs -> FDPE kernels -> SKAG rank-score kernels -> selector
//   start pulse -> done + latency counter + selected path outputs
// Later, this module should sit behind the AWS CL MMIO register wrapper.

module qflow_cloud_kernel #(
    parameter NUM_EDGES      = 8,
    parameter NUM_CAND       = 4,
    parameter MAX_PATH_EDGES = 4,
    parameter EDGE_ID_W      = 4,
    parameter FID_W          = 16,
    parameter SCORE_W        = 32
)(
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire [5:0] src_node,
    input wire [5:0] dst_node,
    input wire [31:0] time_now,
    input wire [FID_W-1:0] f_min_threshold,

    input wire [NUM_EDGES*16-1:0] key_counts_flat,
    input wire [NUM_EDGES*FID_W-1:0] f_init_flat,
    input wire [NUM_EDGES*8-1:0] decay_idx_flat,
    input wire [NUM_EDGES*16-1:0] arrival_rate_flat,
    input wire [NUM_EDGES*FID_W-1:0] qber_flat,
    input wire [NUM_EDGES*SCORE_W-1:0] distance_cost_flat,

    input wire [NUM_CAND*MAX_PATH_EDGES*EDGE_ID_W-1:0] cand_edges_flat,
    input wire [NUM_CAND*3-1:0] cand_lens_flat,

    output reg done,
    output reg valid_path,
    output reg no_path,
    output reg [1:0] selected_path_id,
    output reg [SCORE_W-1:0] best_weight,
    output reg [FID_W-1:0] bottleneck_fidelity,
    output reg [31:0] latency_cycles
);
    wire [NUM_EDGES*FID_W-1:0]   edge_fids_flat;
    wire [NUM_EDGES*SCORE_W-1:0] edge_scores_flat;
    wire [NUM_EDGES-1:0]         edge_valid_flat;

    wire [1:0] selector_path_id;
    wire [SCORE_W-1:0] selector_best_weight;
    wire [FID_W-1:0] selector_bottleneck;
    wire selector_valid;

    reg running;

    genvar i;
    generate
        for (i = 0; i < NUM_EDGES; i = i + 1) begin : EDGE_PIPE
            fdpe_kernel u_fdpe (
                .f_init_q016(f_init_flat[i*FID_W +: FID_W]),
                .decay_idx(decay_idx_flat[i*8 +: 8]),
                .fidelity_q016(edge_fids_flat[i*FID_W +: FID_W])
            );

            skag_weight_kernel u_weight (
                .key_count(key_counts_flat[i*16 +: 16]),
                .fidelity_q016(edge_fids_flat[i*FID_W +: FID_W]),
                .arrival_rate_q8_8(arrival_rate_flat[i*16 +: 16]),
                .qber_q016(qber_flat[i*FID_W +: FID_W]),
                .distance_cost_q16_16(distance_cost_flat[i*SCORE_W +: SCORE_W]),
                .f_min_threshold(f_min_threshold),
                .edge_score(edge_scores_flat[i*SCORE_W +: SCORE_W]),
                .edge_fidelity(),
                .edge_valid(edge_valid_flat[i])
            );
        end
    endgenerate

    path_selector_kernel u_selector (
        .edge_scores_flat(edge_scores_flat),
        .edge_fids_flat(edge_fids_flat),
        .edge_valid_flat(edge_valid_flat),
        .cand_edges_flat(cand_edges_flat),
        .cand_lens_flat(cand_lens_flat),
        .selected_path_id(selector_path_id),
        .best_weight(selector_best_weight),
        .bottleneck_fidelity(selector_bottleneck),
        .valid_path(selector_valid)
    );

    // Minimal 2-cycle transaction model for the first local and AWS register test.
    // time_now/src_node/dst_node are preserved in the interface for traceability;
    // this starter combinational datapath does not yet depend on them.
    always @(posedge clk) begin
        if (!rst_n) begin
            running             <= 1'b0;
            done                <= 1'b0;
            valid_path          <= 1'b0;
            no_path             <= 1'b0;
            selected_path_id    <= 2'd0;
            best_weight         <= 32'd0;
            bottleneck_fidelity <= 16'd0;
            latency_cycles      <= 32'd0;
        end else begin
            if (start && !running) begin
                running        <= 1'b1;
                done           <= 1'b0;
                latency_cycles <= 32'd1;
            end else if (running) begin
                selected_path_id    <= selector_path_id;
                best_weight         <= selector_best_weight;
                bottleneck_fidelity <= selector_bottleneck;
                valid_path          <= selector_valid;
                no_path             <= !selector_valid;
                latency_cycles      <= latency_cycles + 32'd1;
                done                <= 1'b1;
                running             <= 1'b0;
            end else begin
                done <= 1'b0;
            end
        end
    end
endmodule
