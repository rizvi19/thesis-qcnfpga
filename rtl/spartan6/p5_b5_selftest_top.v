`timescale 1ns / 1ps

module p5_b5_selftest_top (
    input  wire       clk_100mhz,
    input  wire       btn_reset,
    output wire       led_heartbeat,
    output wire       led_pass,
    output wire       led_fail,
    output wire       led_done,
    output wire [7:0] seg_n,
    output wire [3:0] an_n
);

    localparam [4:0] LAST_TEST = 5'd16;

    reg [25:0] heartbeat;
    reg [4:0]  test_id;
    reg        start;
    reg        pass;
    reg        fail;
    reg        finished;

    reg [7:0] target_state;
    reg       input_valid;

    reg        c0_valid;
    reg [31:0] c0_cost;
    reg [15:0] c0_fidelity;
    reg [31:0] c0_utilization;
    reg [2:0]  c0_hops;
    reg [1:0]  c0_slot;

    reg        c1_valid;
    reg [31:0] c1_cost;
    reg [15:0] c1_fidelity;
    reg [31:0] c1_utilization;
    reg [2:0]  c1_hops;
    reg [1:0]  c1_slot;

    reg [1:0] expected_profile;
    reg [1:0] expected_slot;
    reg       expected_no_path;
    reg       expected_invalid;

    wire [15:0] min_key;
    wire [15:0] state_fidelity;
    wire [15:0] offered_load;
    wire [15:0] state_imbalance;

    wire ready;
    wire busy;
    wire done;
    wire route_valid;
    wire no_path;
    wire stall;
    wire invalid_request;
    wire [2:0] policy_id;
    wire [7:0] state_id;
    wire [1:0] profile_id;
    wire [1:0] selected_slot;
    wire [17:0] selected_score;
    wire [15:0] bottleneck_fidelity;
    wire [2:0] status;
    wire [15:0] cycles;
    wire cycles_valid;

    function [15:0] key_or_load_code;
        input [1:0] bin;
        begin
            case (bin)
                2'd0: key_or_load_code = 16'd0;
                2'd1: key_or_load_code = 16'd16384;
                2'd2: key_or_load_code = 16'd32768;
                default: key_or_load_code = 16'd49151;
            endcase
        end
    endfunction

    function [15:0] fidelity_code;
        input [1:0] bin;
        begin
            case (bin)
                2'd0: fidelity_code = 16'd0;
                2'd1: fidelity_code = 16'd58982;
                2'd2: fidelity_code = 16'd60948;
                default: fidelity_code = 16'd62914;
            endcase
        end
    endfunction

    function [15:0] imbalance_code;
        input [1:0] bin;
        begin
            case (bin)
                2'd0: imbalance_code = 16'd0;
                2'd1: imbalance_code = 16'd8192;
                2'd2: imbalance_code = 16'd16384;
                default: imbalance_code = 16'd32768;
            endcase
        end
    endfunction

    assign min_key         = key_or_load_code(target_state[7:6]);
    assign state_fidelity  = fidelity_code(target_state[5:4]);
    assign offered_load    = key_or_load_code(target_state[3:2]);
    assign state_imbalance = imbalance_code(target_state[1:0]);

    wire result_mismatch =
        expected_invalid ?
            (!invalid_request || route_valid || no_path || (status != 3'd2)) :
        expected_no_path ?
            (invalid_request || route_valid || !no_path ||
             (status != 3'd1) || (policy_id != 3'd4) ||
             (state_id != target_state) ||
             (profile_id != expected_profile)) :
            (invalid_request || !route_valid || no_path ||
             (status != 3'd0) || (policy_id != 3'd4) ||
             (state_id != target_state) ||
             (profile_id != expected_profile) ||
             (selected_slot != expected_slot) ||
             (selected_score != 18'd0) ||
             (bottleneck_fidelity != 16'd62000));

    p5_b5_policy_shell #(
        .POLICY_MODE(3'd4)
    ) shell (
        .clk(clk_100mhz),
        .rst(btn_reset),
        .start(start),
        .input_valid(input_valid),

        .min_key_occupancy_u16(min_key),
        .bottleneck_fidelity_state_u16(state_fidelity),
        .offered_request_load_u16(offered_load),
        .utilization_imbalance_state_u16(state_imbalance),

        .c0_valid(c0_valid),
        .c0_cost(c0_cost),
        .c0_fidelity(c0_fidelity),
        .c0_utilization(c0_utilization),
        .c0_hops(c0_hops),
        .c0_slot(c0_slot),

        .c1_valid(c1_valid),
        .c1_cost(c1_cost),
        .c1_fidelity(c1_fidelity),
        .c1_utilization(c1_utilization),
        .c1_hops(c1_hops),
        .c1_slot(c1_slot),

        .ready(ready),
        .busy(busy),
        .done(done),
        .route_valid(route_valid),
        .no_path(no_path),
        .stall(stall),
        .invalid_request(invalid_request),

        .policy_id(policy_id),
        .state_id(state_id),
        .profile_id(profile_id),
        .selected_slot(selected_slot),
        .selected_score(selected_score),
        .bottleneck_fidelity(bottleneck_fidelity),
        .status(status),
        .cycles(cycles),
        .cycles_valid(cycles_valid)
    );

    p5_b1_sevenseg display (
        .clk(clk_100mhz),
        .rst(btn_reset),
        .value(16'hB510),
        .seg_n(seg_n),
        .an_n(an_n)
    );

    assign led_heartbeat = heartbeat[25];
    assign led_pass      = pass;
    assign led_fail      = fail;
    assign led_done      = finished;

    always @* begin
        target_state      = 8'd0;
        input_valid       = 1'b1;

        c0_valid          = 1'b1;
        c0_cost           = 32'd100;
        c0_fidelity       = 16'd62000;
        c0_utilization    = 32'd10;
        c0_hops           = 3'd2;
        c0_slot           = 2'd0;

        c1_valid          = 1'b0;
        c1_cost           = 32'd200;
        c1_fidelity       = 16'd62000;
        c1_utilization    = 32'd10;
        c1_hops           = 3'd3;
        c1_slot           = 2'd1;

        expected_profile  = 2'd0;
        expected_slot     = 2'd0;
        expected_no_path  = 1'b0;
        expected_invalid  = 1'b0;

        case (test_id)
            // Establish profile 0.
            5'd0: begin
                target_state = 8'd0;
                expected_profile = 2'd0;
            end

            // Policy state 25 proposes profile 1. Dwell holds 0 twice, then switches.
            5'd1: begin
                target_state = 8'd25;
                expected_profile = 2'd0;
            end
            5'd2: begin
                target_state = 8'd25;
                c0_valid = 1'b0;
                c1_valid = 1'b1;
                expected_profile = 2'd0;
                expected_slot = 2'd1;
            end
            5'd3: begin
                target_state = 8'd25;
                expected_profile = 2'd1;
            end

            // Policy state 17 proposes profile 2.
            5'd4: begin
                target_state = 8'd17;
                c0_valid = 1'b0;
                c1_valid = 1'b1;
                expected_profile = 2'd1;
                expected_slot = 2'd1;
            end
            5'd5: begin
                target_state = 8'd17;
                expected_profile = 2'd1;
            end
            5'd6: begin
                target_state = 8'd17;
                c0_valid = 1'b0;
                c1_valid = 1'b1;
                expected_profile = 2'd2;
                expected_slot = 2'd1;
            end

            // Policy state 104 proposes profile 3.
            5'd7: begin
                target_state = 8'd104;
                expected_profile = 2'd2;
            end
            5'd8: begin
                target_state = 8'd104;
                c0_valid = 1'b0;
                c1_valid = 1'b1;
                expected_profile = 2'd2;
                expected_slot = 2'd1;
            end
            5'd9: begin
                target_state = 8'd104;
                expected_profile = 2'd3;
            end

            // Return toward profile 0, including a no-path transaction.
            5'd10: begin
                target_state = 8'd0;
                c0_valid = 1'b0;
                c1_valid = 1'b1;
                expected_profile = 2'd3;
                expected_slot = 2'd1;
            end
            5'd11: begin
                target_state = 8'd0;
                c0_valid = 1'b0;
                c1_valid = 1'b0;
                expected_profile = 2'd3;
                expected_no_path = 1'b1;
            end
            5'd12: begin
                target_state = 8'd0;
                expected_profile = 2'd0;
            end

            // Invalid input must complete without a route or controller update.
            5'd13: begin
                input_valid = 1'b0;
                expected_invalid = 1'b1;
            end

            // Verify dwell state was preserved across invalid input.
            5'd14: begin
                target_state = 8'd25;
                c0_valid = 1'b0;
                c1_valid = 1'b1;
                expected_profile = 2'd0;
                expected_slot = 2'd1;
            end
            5'd15: begin
                target_state = 8'd25;
                expected_profile = 2'd0;
            end
            5'd16: begin
                target_state = 8'd25;
                c0_valid = 1'b0;
                c1_valid = 1'b1;
                expected_profile = 2'd1;
                expected_slot = 2'd1;
            end

            default: begin
                target_state = 8'd0;
            end
        endcase
    end

    always @(posedge clk_100mhz) begin
        if (btn_reset) begin
            heartbeat <= 26'd0;
            test_id    <= 5'd0;
            start      <= 1'b0;
            pass       <= 1'b0;
            fail       <= 1'b0;
            finished   <= 1'b0;
        end else begin
            heartbeat <= heartbeat + 1'b1;
            start <= 1'b0;

            if (!finished && ready && !start)
                start <= 1'b1;

            if (done) begin
                if (result_mismatch || cycles_valid || (cycles != 16'd0))
                    fail <= 1'b1;

                if (test_id == LAST_TEST) begin
                    finished <= 1'b1;
                    pass <= !(fail || result_mismatch ||
                              cycles_valid || (cycles != 16'd0));
                end else begin
                    test_id <= test_id + 1'b1;
                end
            end
        end
    end

endmodule
