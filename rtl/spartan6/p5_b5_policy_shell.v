`timescale 1ns / 1ps

// P5 Step 7 / B5 common H0-H4 policy shell.
// POLICY_MODE: 0=H0 shortest feasible, 1=H1 fixed key-aware,
//              2=H2 fixed QFlow, 3=H3 frozen rules, 4=H4 learned ROM.
module p5_b5_policy_shell #(
    parameter [2:0] POLICY_MODE = 3'd4,
    parameter POLICY_MEM_FILE = "results/rl/p3_export/policy_rom.mem",
    parameter PROFILE_MEM_FILE = "results/rl/p3_export/profile_rom.mem"
) (
    input  wire        clk,
    input  wire        rst,
    input  wire        start,
    input  wire        input_valid,

    input  wire [15:0] min_key_occupancy_u16,
    input  wire [15:0] bottleneck_fidelity_state_u16,
    input  wire [15:0] offered_request_load_u16,
    input  wire [15:0] utilization_imbalance_state_u16,

    input  wire        c0_valid,
    input  wire [31:0] c0_cost,
    input  wire [15:0] c0_fidelity,
    input  wire [31:0] c0_utilization,
    input  wire [2:0]  c0_hops,
    input  wire [1:0]  c0_slot,

    input  wire        c1_valid,
    input  wire [31:0] c1_cost,
    input  wire [15:0] c1_fidelity,
    input  wire [31:0] c1_utilization,
    input  wire [2:0]  c1_hops,
    input  wire [1:0]  c1_slot,

    output wire        ready,
    output wire        busy,
    output reg         done,
    output reg         route_valid,
    output reg         no_path,
    output reg         stall,
    output reg         invalid_request,

    output wire [2:0]  policy_id,
    output reg  [7:0]  state_id,
    output reg  [1:0]  profile_id,
    output reg  [1:0]  selected_slot,
    output reg  [17:0] selected_score,
    output reg  [15:0] bottleneck_fidelity,
    output reg  [2:0]  status,

    // B6 replaces these placeholders with the accepted-edge-to-done counter.
    output wire [15:0] cycles,
    output wire        cycles_valid
);

    localparam [2:0] H0 = 3'd0;
    localparam [2:0] H1 = 3'd1;
    localparam [2:0] H2 = 3'd2;
    localparam [2:0] H3 = 3'd3;
    localparam [2:0] H4 = 3'd4;

    localparam [2:0] STATUS_OK      = 3'd0;
    localparam [2:0] STATUS_NO_PATH = 3'd1;
    localparam [2:0] STATUS_INVALID = 3'd2;

    localparam [3:0] S_IDLE         = 4'd0;
    localparam [3:0] S_WAIT_STATE   = 4'd1;
    localparam [3:0] S_WAIT_PROFILE = 4'd2;
    localparam [3:0] S_WAIT_H4      = 4'd3;
    localparam [3:0] S_START_EVAL   = 4'd4;
    localparam [3:0] S_WAIT_EVAL    = 4'd5;
    localparam [3:0] S_DONE         = 4'd6;
    localparam [3:0] S_INVALID      = 4'd7;

    reg [3:0] shell_state;

    reg        v0_r, v1_r;
    reg [31:0] cost0_r, cost1_r, util0_r, util1_r;
    reg [15:0] fid0_r, fid1_r;
    reg [2:0]  hops0_r, hops1_r;
    reg [1:0]  slot0_r, slot1_r;

    reg [1:0] requested_profile_r;
    reg [1:0] lambda0_r, lambda1_r, lambda2_r;

    reg        result_route_valid;
    reg        result_no_path;
    reg [1:0]  result_slot;
    reg [17:0] result_score;
    reg [15:0] result_fidelity;
    reg [2:0]  result_status;

    wire accept = ready && start;
    wire encoder_en = accept && input_valid;

    wire encoder_valid;
    wire [7:0] encoder_state_id;

    wire profile_en;
    wire profile_valid;
    wire [17:0] profile_payload;

    wire h4_ready;
    wire h4_busy;
    wire h4_done;
    wire h4_output_valid;
    wire h4_invalid_state;
    wire h4_stall;
    wire h4_no_path_out;
    wire [7:0] h4_state_id;
    wire [1:0] h4_proposed_action;
    wire [1:0] h4_selected_action;
    wire [17:0] h4_profile_payload;
    wire h4_switched;
    wire [1:0] h4_dwell_count;

    wire b4_ready;
    wire b4_done;
    wire b4_route_valid;
    wire b4_no_path;
    wire [1:0] b4_selected_slot;
    wire [17:0] b4_selected_score;

    wire h4_start = accept && input_valid && (POLICY_MODE == H4);
    wire b4_start = (shell_state == S_START_EVAL) && b4_ready;

    function [1:0] h3_action;
        input [7:0] sid;
        reg [1:0] key_bin;
        reg [1:0] fid_bin;
        reg [1:0] load_bin;
        reg [1:0] imbalance_bin;
        begin
            key_bin       = sid[7:6];
            fid_bin       = sid[5:4];
            load_bin      = sid[3:2];
            imbalance_bin = sid[1:0];

            if (key_bin == 2'd0)
                h3_action = 2'd1;
            else if (fid_bin <= 2'd1)
                h3_action = 2'd2;
            else if (imbalance_bin >= 2'd2)
                h3_action = 2'd1;
            else if ((load_bin == 2'd3) &&
                     (key_bin >= 2'd2) &&
                     (fid_bin >= 2'd2) &&
                     (imbalance_bin <= 2'd1))
                h3_action = 2'd3;
            else
                h3_action = 2'd0;
        end
    endfunction

    wire [1:0] profile_request =
        (POLICY_MODE == H2) ? 2'd0 : h3_action(encoder_state_id);

    assign ready = (shell_state == S_IDLE);
    assign busy = (shell_state != S_IDLE);
    assign policy_id = POLICY_MODE;
    assign cycles = 16'd0;
    assign cycles_valid = 1'b0;

    assign profile_en =
        (shell_state == S_WAIT_STATE) &&
        encoder_valid &&
        ((POLICY_MODE == H2) || (POLICY_MODE == H3));

    rl_state_encoder state_encoder_i (
        .clk(clk),
        .rst(rst),
        .en(encoder_en),
        .min_key_occupancy_u16(min_key_occupancy_u16),
        .bottleneck_fidelity_u16(bottleneck_fidelity_state_u16),
        .offered_request_load_u16(offered_request_load_u16),
        .utilization_imbalance_u16(utilization_imbalance_state_u16),
        .valid(encoder_valid),
        .state_id(encoder_state_id)
    );

    rl_profile_rom #(
        .MEM_FILE(PROFILE_MEM_FILE)
    ) profile_rom_i (
        .clk(clk),
        .rst(rst),
        .en(profile_en),
        .selected_action(profile_request),
        .valid(profile_valid),
        .profile_payload(profile_payload)
    );

    rl_controller h4_controller_i (
        .clk(clk),
        .rst(rst),
        .start(h4_start),
        .input_valid(input_valid),
        .no_path_in(!(c0_valid || c1_valid)),
        .min_key_occupancy_u16(min_key_occupancy_u16),
        .bottleneck_fidelity_u16(bottleneck_fidelity_state_u16),
        .offered_request_load_u16(offered_request_load_u16),
        .utilization_imbalance_u16(utilization_imbalance_state_u16),
        .ready(h4_ready),
        .busy(h4_busy),
        .done(h4_done),
        .output_valid(h4_output_valid),
        .invalid_state(h4_invalid_state),
        .stall(h4_stall),
        .no_path_out(h4_no_path_out),
        .state_id(h4_state_id),
        .proposed_action(h4_proposed_action),
        .selected_action(h4_selected_action),
        .profile_payload(h4_profile_payload),
        .switched(h4_switched),
        .dwell_count_sat(h4_dwell_count)
    );

    p5_b4_candidate_evaluator evaluator_i (
        .clk(clk),
        .rst(rst),
        .start(b4_start),
        .ready(b4_ready),

        .c0_valid(v0_r),
        .c0_cost(cost0_r),
        .c0_fidelity(fid0_r),
        .c0_utilization(util0_r),
        .c0_hops(hops0_r),
        .c0_slot(slot0_r),

        .c1_valid(v1_r),
        .c1_cost(cost1_r),
        .c1_fidelity(fid1_r),
        .c1_utilization(util1_r),
        .c1_hops(hops1_r),
        .c1_slot(slot1_r),

        .lambda0(lambda0_r),
        .lambda1(lambda1_r),
        .lambda2(lambda2_r),

        .done(b4_done),
        .route_valid(b4_route_valid),
        .no_path(b4_no_path),
        .selected_slot(b4_selected_slot),
        .selected_score(b4_selected_score)
    );

    always @(posedge clk) begin
        if (rst) begin
            shell_state          <= S_IDLE;
            v0_r                 <= 1'b0;
            v1_r                 <= 1'b0;
            cost0_r              <= 32'd0;
            cost1_r              <= 32'd0;
            util0_r              <= 32'd0;
            util1_r              <= 32'd0;
            fid0_r               <= 16'd0;
            fid1_r               <= 16'd0;
            hops0_r              <= 3'd0;
            hops1_r              <= 3'd0;
            slot0_r              <= 2'd0;
            slot1_r              <= 2'd1;
            requested_profile_r  <= 2'd0;
            lambda0_r            <= 2'd0;
            lambda1_r            <= 2'd0;
            lambda2_r            <= 2'd0;
            result_route_valid   <= 1'b0;
            result_no_path       <= 1'b0;
            result_slot          <= 2'd0;
            result_score         <= 18'd0;
            result_fidelity      <= 16'd0;
            result_status        <= STATUS_OK;
            done                 <= 1'b0;
            route_valid          <= 1'b0;
            no_path              <= 1'b0;
            stall                <= 1'b0;
            invalid_request      <= 1'b0;
            state_id             <= 8'd0;
            profile_id           <= 2'd0;
            selected_slot        <= 2'd0;
            selected_score       <= 18'd0;
            bottleneck_fidelity  <= 16'd0;
            status               <= STATUS_OK;
        end else begin
            done            <= 1'b0;
            route_valid     <= 1'b0;
            no_path         <= 1'b0;
            stall           <= 1'b0;
            invalid_request <= 1'b0;

            if ((shell_state != S_IDLE) && start)
                stall <= 1'b1;

            case (shell_state)
                S_IDLE: begin
                    if (start) begin
                        if (!input_valid) begin
                            shell_state <= S_INVALID;
                        end else begin
                            v0_r    <= c0_valid;
                            v1_r    <= c1_valid;
                            cost0_r <= c0_cost;
                            cost1_r <= c1_cost;
                            fid0_r  <= c0_fidelity;
                            fid1_r  <= c1_fidelity;
                            util0_r <= c0_utilization;
                            util1_r <= c1_utilization;
                            hops0_r <= c0_hops;
                            hops1_r <= c1_hops;
                            slot0_r <= c0_slot;
                            slot1_r <= c1_slot;
                            shell_state <= S_WAIT_STATE;
                        end
                    end
                end

                S_WAIT_STATE: begin
                    if (encoder_valid) begin
                        state_id <= encoder_state_id;
                        case (POLICY_MODE)
                            H0: begin
                                profile_id <= 2'd0;
                                result_score <= 18'd0;
                                if (!v0_r && !v1_r) begin
                                    result_route_valid <= 1'b0;
                                    result_no_path <= 1'b1;
                                    result_slot <= 2'd0;
                                    result_fidelity <= 16'd0;
                                    result_status <= STATUS_NO_PATH;
                                end else if (v0_r && !v1_r) begin
                                    result_route_valid <= 1'b1;
                                    result_no_path <= 1'b0;
                                    result_slot <= slot0_r;
                                    result_fidelity <= fid0_r;
                                    result_status <= STATUS_OK;
                                end else if (!v0_r && v1_r) begin
                                    result_route_valid <= 1'b1;
                                    result_no_path <= 1'b0;
                                    result_slot <= slot1_r;
                                    result_fidelity <= fid1_r;
                                    result_status <= STATUS_OK;
                                end else if ((hops0_r < hops1_r) ||
                                             ((hops0_r == hops1_r) &&
                                              (slot0_r <= slot1_r))) begin
                                    result_route_valid <= 1'b1;
                                    result_no_path <= 1'b0;
                                    result_slot <= slot0_r;
                                    result_fidelity <= fid0_r;
                                    result_status <= STATUS_OK;
                                end else begin
                                    result_route_valid <= 1'b1;
                                    result_no_path <= 1'b0;
                                    result_slot <= slot1_r;
                                    result_fidelity <= fid1_r;
                                    result_status <= STATUS_OK;
                                end
                                shell_state <= S_DONE;
                            end

                            H1: begin
                                profile_id <= 2'd0;
                                lambda0_r <= 2'd1;
                                lambda1_r <= 2'd0;
                                lambda2_r <= 2'd0;
                                shell_state <= S_START_EVAL;
                            end

                            H2: begin
                                requested_profile_r <= 2'd0;
                                shell_state <= S_WAIT_PROFILE;
                            end

                            H3: begin
                                requested_profile_r <= h3_action(encoder_state_id);
                                shell_state <= S_WAIT_PROFILE;
                            end

                            default: begin
                                shell_state <= S_WAIT_H4;
                            end
                        endcase
                    end
                end

                S_WAIT_PROFILE: begin
                    if (profile_valid) begin
                        profile_id <= requested_profile_r;
                        lambda0_r <= profile_payload[5:4];
                        lambda1_r <= profile_payload[3:2];
                        lambda2_r <= profile_payload[1:0];
                        shell_state <= S_START_EVAL;
                    end
                end

                S_WAIT_H4: begin
                    if (h4_done) begin
                        state_id <= h4_state_id;
                        profile_id <= h4_selected_action;
                        lambda0_r <= h4_profile_payload[5:4];
                        lambda1_r <= h4_profile_payload[3:2];
                        lambda2_r <= h4_profile_payload[1:0];
                        shell_state <= S_START_EVAL;
                    end
                end

                S_START_EVAL: begin
                    if (b4_ready)
                        shell_state <= S_WAIT_EVAL;
                end

                S_WAIT_EVAL: begin
                    if (b4_done) begin
                        result_route_valid <= b4_route_valid;
                        result_no_path <= b4_no_path;
                        result_slot <= b4_selected_slot;
                        result_score <= b4_selected_score;

                        if (b4_route_valid && (b4_selected_slot == slot0_r))
                            result_fidelity <= fid0_r;
                        else if (b4_route_valid && (b4_selected_slot == slot1_r))
                            result_fidelity <= fid1_r;
                        else
                            result_fidelity <= 16'd0;

                        result_status <= b4_no_path ? STATUS_NO_PATH : STATUS_OK;
                        shell_state <= S_DONE;
                    end
                end

                S_DONE: begin
                    done <= 1'b1;
                    route_valid <= result_route_valid;
                    no_path <= result_no_path;
                    selected_slot <= result_slot;
                    selected_score <= result_score;
                    bottleneck_fidelity <= result_fidelity;
                    status <= result_status;
                    shell_state <= S_IDLE;
                end

                S_INVALID: begin
                    done <= 1'b1;
                    invalid_request <= 1'b1;
                    route_valid <= 1'b0;
                    no_path <= 1'b0;
                    selected_slot <= 2'd0;
                    selected_score <= 18'd0;
                    bottleneck_fidelity <= 16'd0;
                    status <= STATUS_INVALID;
                    shell_state <= S_IDLE;
                end

                default: begin
                    shell_state <= S_IDLE;
                end
            endcase
        end
    end

endmodule
