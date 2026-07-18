`timescale 1ns / 1ps

// QFlow-RL P4 four-entry profile ROM.
// Each action-major entry contains one exact 18-bit frozen coefficient payload.
module rl_profile_rom #(
    parameter MEM_FILE = "results/rl/p3_export/profile_rom.mem"
) (
    input  wire        clk,
    input  wire        rst,
    input  wire        en,
    input  wire [1:0]  selected_action,
    output reg         valid,
    output reg  [17:0] profile_payload
);

    reg [17:0] profile_mem [0:3];

    initial begin
        $readmemh(MEM_FILE, profile_mem);
    end

    always @(posedge clk) begin
        if (rst) begin
            valid           <= 1'b0;
            profile_payload <= 18'd0;
        end else begin
            valid <= en;
            if (en)
                profile_payload <= profile_mem[selected_action];
        end
    end

endmodule
