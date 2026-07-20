`timescale 1ns / 1ps

// P5 Step 8 / B6 measurement wrapper.
//
// The wrapped B5 policy shell remains unchanged. This wrapper measures only
// synchronous kernel latency. A request is accepted at edge N when
// start && ready is true. During the one-cycle done pulse, cycles equals
// N_done - N and cycles_valid is asserted. UART serialization, host parsing,
// programming and human observation are outside this counter.
module p5_b6_measurement_shell #(
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
    output wire        done,
    output wire        route_valid,
    output wire        no_path,
    output wire        stall,
    output wire        invalid_request,

    output wire [2:0]  policy_id,
    output wire [7:0]  state_id,
    output wire [1:0]  profile_id,
    output wire [1:0]  selected_slot,
    output wire [17:0] selected_score,
    output wire [15:0] bottleneck_fidelity,
    output wire [2:0]  status,

    output wire [15:0] cycles,
    output wire        cycles_valid
);

    reg        measurement_active;
    reg [15:0] kernel_cycle_counter;

    wire [15:0] ignored_b5_cycles;
    wire        ignored_b5_cycles_valid;

    wire accepted = start && ready;

    assign cycles = kernel_cycle_counter;
    assign cycles_valid = done;

    p5_b5_policy_shell #(
        .POLICY_MODE(POLICY_MODE),
        .POLICY_MEM_FILE(POLICY_MEM_FILE),
        .PROFILE_MEM_FILE(PROFILE_MEM_FILE)
    ) core (
        .clk(clk),
        .rst(rst),
        .start(start),
        .input_valid(input_valid),

        .min_key_occupancy_u16(min_key_occupancy_u16),
        .bottleneck_fidelity_state_u16(bottleneck_fidelity_state_u16),
        .offered_request_load_u16(offered_request_load_u16),
        .utilization_imbalance_state_u16(utilization_imbalance_state_u16),

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

        .cycles(ignored_b5_cycles),
        .cycles_valid(ignored_b5_cycles_valid)
    );

    always @(posedge clk) begin
        if (rst) begin
            measurement_active  <= 1'b0;
            kernel_cycle_counter <= 16'd0;
        end else begin
            if (accepted) begin
                measurement_active  <= 1'b1;
                kernel_cycle_counter <= 16'd0;
            end else if (measurement_active && !done) begin
                if (kernel_cycle_counter != 16'hffff)
                    kernel_cycle_counter <= kernel_cycle_counter + 1'b1;
            end

            if (measurement_active && done)
                measurement_active <= 1'b0;
        end
    end

endmodule
