`timescale 1ns / 1ps

// QFlow-RL P4 deterministic learned-policy controller.
// Three registered stages: state encoder, policy ROM, selected profile ROM.
module rl_controller (
    input  wire        clk,
    input  wire        rst,
    input  wire        start,
    input  wire        input_valid,
    input  wire        no_path_in,
    input  wire [15:0] min_key_occupancy_u16,
    input  wire [15:0] bottleneck_fidelity_u16,
    input  wire [15:0] offered_request_load_u16,
    input  wire [15:0] utilization_imbalance_u16,
    output wire        ready,
    output wire        busy,
    output reg         done,
    output reg         output_valid,
    output reg         invalid_state,
    output reg         stall,
    output reg         no_path_out,
    output reg  [7:0]  state_id,
    output reg  [1:0]  proposed_action,
    output reg  [1:0]  selected_action,
    output reg  [17:0] profile_payload,
    output reg         switched,
    output reg  [1:0]  dwell_count_sat
);

    localparam [1:0] STATE_IDLE         = 2'd0;
    localparam [1:0] STATE_WAIT_POLICY  = 2'd1;
    localparam [1:0] STATE_WAIT_PROFILE = 2'd2;
    localparam [1:0] STATE_INVALID      = 2'd3;

    reg [1:0] controller_state;
    reg       no_path_latched;
    reg       current_action_valid;
    reg [1:0] current_action;
    reg [1:0] current_dwell_count;

    reg [7:0] transaction_state_id;
    reg [1:0] transaction_proposed_action;
    reg [1:0] transaction_selected_action;
    reg       transaction_switched;
    reg [1:0] transaction_dwell_count;

    wire       encoder_en;
    wire       encoder_valid;
    wire [7:0] encoder_state_id;
    wire       policy_en;
    wire       policy_valid;
    wire [1:0] policy_proposed_action;
    wire       profile_en;
    wire       profile_valid;
    wire [17:0] profile_payload_internal;

    wire       eligible_change;
    wire [1:0] dwell_selected_action;
    wire [1:0] dwell_next_count;
    wire       dwell_switched;

    assign ready = (controller_state == STATE_IDLE);
    assign busy  = (controller_state != STATE_IDLE);

    assign encoder_en = ready && start && input_valid;
    assign policy_en = (controller_state == STATE_WAIT_POLICY) && encoder_valid;
    assign profile_en = (controller_state == STATE_WAIT_POLICY) && policy_valid;

    assign eligible_change = current_action_valid &&
                             (policy_proposed_action != current_action) &&
                             (current_dwell_count >= 2'd3);
    assign dwell_selected_action = !current_action_valid ? policy_proposed_action :
                                   eligible_change ? policy_proposed_action : current_action;
    assign dwell_switched = eligible_change;
    assign dwell_next_count = !current_action_valid ? 2'd1 :
                              eligible_change ? 2'd1 :
                              (current_dwell_count < 2'd3) ?
                                  (current_dwell_count + 2'd1) : 2'd3;

    rl_state_encoder state_encoder_i (
        .clk(clk),
        .rst(rst),
        .en(encoder_en),
        .min_key_occupancy_u16(min_key_occupancy_u16),
        .bottleneck_fidelity_u16(bottleneck_fidelity_u16),
        .offered_request_load_u16(offered_request_load_u16),
        .utilization_imbalance_u16(utilization_imbalance_u16),
        .valid(encoder_valid),
        .state_id(encoder_state_id)
    );

    rl_policy_rom policy_rom_i (
        .clk(clk),
        .rst(rst),
        .en(policy_en),
        .state_id(encoder_state_id),
        .valid(policy_valid),
        .proposed_action(policy_proposed_action)
    );

    rl_profile_rom profile_rom_i (
        .clk(clk),
        .rst(rst),
        .en(profile_en),
        .selected_action(dwell_selected_action),
        .valid(profile_valid),
        .profile_payload(profile_payload_internal)
    );

    always @(posedge clk) begin
        if (rst) begin
            controller_state             <= STATE_IDLE;
            no_path_latched              <= 1'b0;
            current_action_valid         <= 1'b0;
            current_action               <= 2'd0;
            current_dwell_count          <= 2'd0;
            transaction_state_id         <= 8'd0;
            transaction_proposed_action  <= 2'd0;
            transaction_selected_action  <= 2'd0;
            transaction_switched         <= 1'b0;
            transaction_dwell_count      <= 2'd0;
            done                         <= 1'b0;
            output_valid                 <= 1'b0;
            invalid_state                <= 1'b0;
            stall                        <= 1'b0;
            no_path_out                  <= 1'b0;
            state_id                     <= 8'd0;
            proposed_action              <= 2'd0;
            selected_action              <= 2'd0;
            profile_payload              <= 18'd0;
            switched                     <= 1'b0;
            dwell_count_sat              <= 2'd0;
        end else begin
            done          <= 1'b0;
            output_valid  <= 1'b0;
            invalid_state <= 1'b0;
            stall         <= 1'b0;
            no_path_out   <= 1'b0;
            switched      <= 1'b0;

            if ((controller_state != STATE_IDLE) && start)
                stall <= 1'b1;

            case (controller_state)
                STATE_IDLE: begin
                    if (start) begin
                        if (input_valid) begin
                            no_path_latched <= no_path_in;
                            controller_state <= STATE_WAIT_POLICY;
                        end else begin
                            controller_state <= STATE_INVALID;
                        end
                    end
                end

                STATE_WAIT_POLICY: begin
                    if (encoder_valid)
                        transaction_state_id <= encoder_state_id;
                    if (policy_valid) begin
                        transaction_proposed_action <= policy_proposed_action;
                        transaction_selected_action <= dwell_selected_action;
                        transaction_switched        <= dwell_switched;
                        transaction_dwell_count     <= dwell_next_count;
                        current_action_valid        <= 1'b1;
                        current_action              <= dwell_selected_action;
                        current_dwell_count         <= dwell_next_count;
                        controller_state            <= STATE_WAIT_PROFILE;
                    end
                end

                STATE_WAIT_PROFILE: begin
                    if (profile_valid) begin
                        done            <= 1'b1;
                        output_valid    <= 1'b1;
                        no_path_out     <= no_path_latched;
                        state_id        <= transaction_state_id;
                        proposed_action <= transaction_proposed_action;
                        selected_action <= transaction_selected_action;
                        profile_payload <= profile_payload_internal;
                        switched        <= transaction_switched;
                        dwell_count_sat <= transaction_dwell_count;
                        controller_state <= STATE_IDLE;
                    end
                end

                STATE_INVALID: begin
                    done             <= 1'b1;
                    invalid_state    <= 1'b1;
                    controller_state <= STATE_IDLE;
                end

                default: begin
                    controller_state <= STATE_IDLE;
                end
            endcase
        end
    end

endmodule
