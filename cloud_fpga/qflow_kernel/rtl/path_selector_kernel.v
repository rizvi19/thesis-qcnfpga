`timescale 1ns/1ps
// -----------------------------------------------------------------------------
// QFlow AWS F2 starter kernel - candidate path selector
// -----------------------------------------------------------------------------
// Evaluates NUM_CAND candidate paths. Each candidate is a sequence of edge IDs.
// It rejects invalid/blocked paths and selects the valid path with minimum total
// score. Bottleneck fidelity is the minimum edge fidelity along the selected path.
//
// Lint-cleaning note:
// All temporary variables are assigned deterministic defaults on every
// combinational evaluation path to avoid unintended latch inference.

module path_selector_kernel #(
    parameter NUM_EDGES      = 8,
    parameter NUM_CAND       = 4,
    parameter MAX_PATH_EDGES = 4,
    parameter EDGE_ID_W      = 4,
    parameter SCORE_W        = 32,
    parameter FID_W          = 16,
    parameter INF_SCORE      = 32'hFFFF_FFFF
)(
    input wire [NUM_EDGES*SCORE_W-1:0] edge_scores_flat,
    input wire [NUM_EDGES*FID_W-1:0]   edge_fids_flat,
    input wire [NUM_EDGES-1:0]         edge_valid_flat,
    input wire [NUM_CAND*MAX_PATH_EDGES*EDGE_ID_W-1:0] cand_edges_flat,
    input wire [NUM_CAND*3-1:0]        cand_lens_flat,
    output reg [1:0]                   selected_path_id,
    output reg [SCORE_W-1:0]           best_weight,
    output reg [FID_W-1:0]             bottleneck_fidelity,
    output reg                         valid_path
);
    integer c;
    integer k;

    reg [EDGE_ID_W-1:0] eid;
    reg [2:0] cand_len;
    reg [SCORE_W-1:0] cand_score;
    reg [FID_W-1:0] cand_bottleneck;
    reg cand_valid;

    reg [SCORE_W-1:0] edge_score;
    reg [FID_W-1:0] edge_fid;
    reg edge_valid;

    // NUM_EDGES=8 in the first AWS cloud kernel, so 3 bits are enough.
    // Keeping this explicit avoids using a 4-bit edge ID directly as an
    // index into an 8-bit vector.
    reg [2:0] eid_idx;

    always @* begin
        selected_path_id     = 2'd0;
        best_weight          = INF_SCORE;
        bottleneck_fidelity  = {FID_W{1'b0}};
        valid_path           = 1'b0;

        // Defaults for temporaries. These are overwritten inside the loops
        // when the corresponding candidate edge is active and valid.
        eid             = {EDGE_ID_W{1'b0}};
        eid_idx         = 3'd0;
        cand_len        = 3'd0;
        cand_score      = {SCORE_W{1'b0}};
        cand_bottleneck = {FID_W{1'b1}};
        cand_valid      = 1'b0;
        edge_score      = INF_SCORE;
        edge_fid        = {FID_W{1'b0}};
        edge_valid      = 1'b0;

        for (c = 0; c < NUM_CAND; c = c + 1) begin
            cand_len        = cand_lens_flat[c*3 +: 3];
            cand_score      = {SCORE_W{1'b0}};
            cand_bottleneck = {FID_W{1'b1}};
            cand_valid      = (cand_len != 3'd0);

            for (k = 0; k < MAX_PATH_EDGES; k = k + 1) begin
                // Per-iteration defaults prevent latch inference for
                // temporary edge-read values when k >= cand_len.
                eid        = {EDGE_ID_W{1'b0}};
                eid_idx    = 3'd0;
                edge_score = INF_SCORE;
                edge_fid   = {FID_W{1'b0}};
                edge_valid = 1'b0;

                if (k < cand_len) begin
                    eid = cand_edges_flat[(c*MAX_PATH_EDGES + k)*EDGE_ID_W +: EDGE_ID_W];

                    if (eid >= NUM_EDGES[EDGE_ID_W-1:0]) begin
                        cand_valid = 1'b0;
                    end else begin
                        eid_idx    = eid[2:0];
                        edge_score = edge_scores_flat[eid_idx*SCORE_W +: SCORE_W];
                        edge_fid   = edge_fids_flat[eid_idx*FID_W +: FID_W];
                        edge_valid = edge_valid_flat[eid_idx];

                        if (!edge_valid || edge_score == INF_SCORE) begin
                            cand_valid = 1'b0;
                        end else begin
                            cand_score = cand_score + edge_score;
                            if (edge_fid < cand_bottleneck) begin
                                cand_bottleneck = edge_fid;
                            end
                        end
                    end
                end
            end

            if (cand_valid && (!valid_path || cand_score < best_weight)) begin
                valid_path          = 1'b1;
                selected_path_id    = c[1:0];
                best_weight         = cand_score;
                bottleneck_fidelity = cand_bottleneck;
            end
        end
    end
endmodule
