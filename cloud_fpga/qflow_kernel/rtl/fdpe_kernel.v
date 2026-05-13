`timescale 1ns/1ps
// -----------------------------------------------------------------------------
// QFlow AWS F2 starter kernel - FDPE-style fidelity update
// -----------------------------------------------------------------------------
// Computes: fidelity_q016 = f_init_q016 * exp_lut[decay_idx] >> 16
// This is the small cloud-validation primitive. It preserves the Q0.16 fidelity
// contract and 256-entry exp(-x) LUT idea, while exposing a simple deterministic
// input interface for host-to-FPGA vector tests.

module fdpe_kernel #(
    parameter LUT_DEPTH = 256,
    parameter FID_W     = 16
)(
    input  wire [FID_W-1:0] f_init_q016,
    input  wire [7:0]       decay_idx,
    output wire [FID_W-1:0] fidelity_q016
);
    reg [FID_W-1:0] exp_lut [0:LUT_DEPTH-1];
    wire [31:0] product;

    initial begin
        $readmemh("vectors/exp_lut.hex", exp_lut);
    end

    assign product       = f_init_q016 * exp_lut[decay_idx];
    assign fidelity_q016 = product[31:16];
endmodule
