`timescale 1ns / 1ps

// QFlow-RL P4 learned policy-index ROM.
// The memory file is the frozen P3 deployment artifact: 256 state-major
// entries, one hexadecimal digit per line, with two useful action bits.
module rl_policy_rom #(
    parameter MEM_FILE = "results/rl/p3_export/policy_rom.mem"
) (
    input  wire       clk,
    input  wire       rst,
    input  wire       en,
    input  wire [7:0] state_id,
    output reg        valid,
    output reg  [1:0] proposed_action
);

    reg [1:0] policy_mem [0:255];

    initial begin
        $readmemh(MEM_FILE, policy_mem);
    end

    always @(posedge clk) begin
        if (rst) begin
            valid           <= 1'b0;
            proposed_action <= 2'd0;
        end else begin
            valid <= en;
            if (en)
                proposed_action <= policy_mem[state_id];
        end
    end

endmodule
