`timescale 1ns / 1ps

module p5_b6_selftest_top (
    input  wire       clk_100mhz,
    input  wire       btn_reset,
    output wire       led_heartbeat,
    output wire       led_pass,
    output wire       led_fail,
    output wire       led_done,
    output wire [7:0] seg_n,
    output wire [3:0] an_n
);

    localparam [2:0] LAST_TEST = 3'd4;

    reg [25:0] heartbeat;
    reg [2:0]  test_id;
    reg        start;
    reg        pass;
    reg        fail;
    reg        finished;

    reg        input_valid;
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

    reg [15:0] expected_cycles;
    reg        expected_route_valid;
    reg        expected_no_path;
    reg        expected_invalid;
    reg [1:0]  expected_slot;
    reg [2:0]  expected_status;

    wire ready;
    wire busy;
    wire done;
    wire route_valid;
    wire no_path;
    wire stall;
    wire invalid_request;

    wire [2:0]  policy_id;
    wire [7:0]  state_id;
    wire [1:0]  profile_id;
    wire [1:0]  selected_slot;
    wire [17:0] selected_score;
    wire [15:0] bottleneck_fidelity;
    wire [2:0]  status;
    wire [15:0] cycles;
    wire        cycles_valid;

    wire result_mismatch =
        !cycles_valid ||
        (cycles != expected_cycles) ||
        (route_valid != expected_route_valid) ||
        (no_path != expected_no_path) ||
        (invalid_request != expected_invalid) ||
        (status != expected_status) ||
        (policy_id != 3'd4) ||
        (!expected_invalid && (state_id != 8'd0)) ||
        (!expected_invalid && (profile_id != 2'd0)) ||
        (expected_route_valid && (selected_slot != expected_slot));

    p5_b6_measurement_shell #(
        .POLICY_MODE(3'd4)
    ) measured_shell (
        .clk(clk_100mhz),
        .rst(btn_reset),
        .start(start),
        .input_valid(input_valid),

        .min_key_occupancy_u16(16'd0),
        .bottleneck_fidelity_state_u16(16'd0),
        .offered_request_load_u16(16'd0),
        .utilization_imbalance_state_u16(16'd0),

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
        .value(16'hB610),
        .seg_n(seg_n),
        .an_n(an_n)
    );

    assign led_heartbeat = heartbeat[25];
    assign led_pass      = pass;
    assign led_fail      = fail;
    assign led_done      = finished;

    always @* begin
        input_valid         = 1'b1;

        c0_valid            = 1'b1;
        c0_cost             = 32'd100;
        c0_fidelity         = 16'd62000;
        c0_utilization      = 32'd10;
        c0_hops             = 3'd3;
        c0_slot             = 2'd0;

        c1_valid            = 1'b0;
        c1_cost             = 32'd200;
        c1_fidelity         = 16'd62000;
        c1_utilization      = 32'd10;
        c1_hops             = 3'd2;
        c1_slot             = 2'd1;

        expected_cycles     = 16'd10;
        expected_route_valid = 1'b1;
        expected_no_path    = 1'b0;
        expected_invalid    = 1'b0;
        expected_slot       = 2'd0;
        expected_status     = 3'd0;

        case (test_id)
            // Single candidate, accepted edge to H4 done edge = 10 cycles.
            3'd0: begin
                expected_cycles = 16'd10;
            end

            // Candidate 1 only.
            3'd1: begin
                c0_valid = 1'b0;
                c1_valid = 1'b1;
                expected_cycles = 16'd10;
                expected_slot = 2'd1;
            end

            // Two candidates exercise the full iterative B4 path.
            3'd2: begin
                c0_valid = 1'b1;
                c1_valid = 1'b1;
                expected_cycles = 16'd112;
                expected_slot = 2'd0;
            end

            // No feasible route.
            3'd3: begin
                c0_valid = 1'b0;
                c1_valid = 1'b0;
                expected_cycles = 16'd9;
                expected_route_valid = 1'b0;
                expected_no_path = 1'b1;
                expected_status = 3'd1;
            end

            // Accepted invalid request completes in one kernel cycle.
            3'd4: begin
                input_valid = 1'b0;
                expected_cycles = 16'd1;
                expected_route_valid = 1'b0;
                expected_invalid = 1'b1;
                expected_status = 3'd2;
            end

            default: begin
                expected_cycles = 16'd10;
            end
        endcase
    end

    always @(posedge clk_100mhz) begin
        if (btn_reset) begin
            heartbeat <= 26'd0;
            test_id    <= 3'd0;
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
                if (result_mismatch)
                    fail <= 1'b1;

                if (test_id == LAST_TEST) begin
                    finished <= 1'b1;
                    pass <= !(fail || result_mismatch);
                end else begin
                    test_id <= test_id + 1'b1;
                end
            end
        end
    end

endmodule
