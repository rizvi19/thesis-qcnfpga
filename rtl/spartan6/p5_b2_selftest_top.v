`timescale 1ns / 1ps

module p5_b2_selftest_top #(
    parameter integer HEARTBEAT_BIT = 25,
    parameter LUT_FILE = "p5_b2_exp_lut.mem"
) (
    input  wire       clk_100mhz,
    input  wire       btn_reset,
    output wire       led_heartbeat,
    output wire       led_pass,
    output wire       led_fail,
    output wire       led_done,
    output wire [7:0] seg_n,
    output wire [3:0] an_n
);

    reg [HEARTBEAT_BIT:0] heartbeat_counter;
    reg core_start;
    reg waiting_for_done;
    reg [4:0] test_index;
    reg [7:0] pass_count;
    reg failed;
    reg all_done;
    reg [49:0] active_vector;
    wire [49:0] selected_vector;
    wire core_ready;
    wire core_busy;
    wire core_done;
    wire core_error;
    wire [15:0] core_fidelity;
    wire [15:0] display_value;

    function [49:0] board_vector;
        input [4:0] vector_index;
        begin
            case (vector_index)
`include "p5_b2_board_vectors.vh"
                default: board_vector = 50'd0;
            endcase
        end
    endfunction

    assign selected_vector = board_vector(test_index);
    assign led_heartbeat = heartbeat_counter[HEARTBEAT_BIT];
    assign led_pass = all_done && !failed && (pass_count == 8'd16);
    assign led_fail = all_done && failed;
    assign led_done = all_done;
    assign display_value = all_done ? {8'hB2, pass_count} : {8'hB2, 3'b000, test_index};

    p5_b2_fdpe #(
        .LUT_FILE(LUT_FILE)
    ) u_fdpe (
        .clk(clk_100mhz),
        .rst(btn_reset),
        .start(core_start),
        .tau_zero(active_vector[49]),
        .x_uq4_12(active_vector[47:32]),
        .f_initial_unorm16(active_vector[31:16]),
        .ready(core_ready),
        .busy(core_busy),
        .done(core_done),
        .error(core_error),
        .fidelity_unorm16(core_fidelity)
    );

    p5_b1_sevenseg u_display (
        .clk(clk_100mhz),
        .rst(btn_reset),
        .value(display_value),
        .seg_n(seg_n),
        .an_n(an_n)
    );

    always @(posedge clk_100mhz) begin
        if (btn_reset) begin
            heartbeat_counter <= {(HEARTBEAT_BIT+1){1'b0}};
            core_start <= 1'b0;
            waiting_for_done <= 1'b0;
            test_index <= 5'd0;
            pass_count <= 8'd0;
            failed <= 1'b0;
            all_done <= 1'b0;
            active_vector <= 50'd0;
        end else begin
            heartbeat_counter <= heartbeat_counter + 1'b1;
            core_start <= 1'b0;
            if (!all_done) begin
                if (!waiting_for_done && core_ready) begin
                    active_vector <= selected_vector;
                    core_start <= 1'b1;
                    waiting_for_done <= 1'b1;
                end
                if (core_done) begin
                    waiting_for_done <= 1'b0;
                    if ((core_fidelity == active_vector[15:0]) &&
                        (core_error == active_vector[48]))
                        pass_count <= pass_count + 1'b1;
                    else
                        failed <= 1'b1;
                    if (test_index == 5'd15)
                        all_done <= 1'b1;
                    else
                        test_index <= test_index + 1'b1;
                end
            end
        end
    end

endmodule
