`timescale 1ns / 1ps

module p5_b2_fdpe #(
    parameter LUT_FILE = "rtl/spartan6/p5_b2_exp_lut.mem"
) (
    input  wire        clk,
    input  wire        rst,
    input  wire        start,
    input  wire        tau_zero,
    input  wire [15:0] x_uq4_12,
    input  wire [15:0] f_initial_unorm16,
    output wire        ready,
    output reg         busy,
    output reg         done,
    output reg         error,
    output reg  [15:0] fidelity_unorm16
);

    (* rom_style = "distributed" *) reg [15:0] exp_lut_a [0:255];
    (* rom_style = "distributed" *) reg [15:0] exp_lut_b [0:255];
    reg [2:0] stage;
    reg [15:0] x_reg;
    reg [15:0] f_reg;
    reg tau_zero_reg;
    reg endpoint_zero_reg;
    reg [7:0] index_reg;
    reg [6:0] fraction_reg;
    reg [15:0] decay_reg;
    reg [15:0] y0_reg;
    reg [15:0] y1_reg;
    reg [16:0] delta_reg;
    reg [31:0] base_reg;
    reg [6:0] fraction_pipe_reg;
    reg [31:0] scaled_delta_reg;
    reg [31:0] base_pipe_reg;
    reg [31:0] interpolation_tmp;
    reg [31:0] rounded_tmp;
    reg [31:0] product_tmp;

    assign ready = ~busy;

    initial begin
        $readmemh(LUT_FILE, exp_lut_a);
        $readmemh(LUT_FILE, exp_lut_b);
    end

    always @(posedge clk) begin
        if (rst) begin
            stage <= 3'd0;
            x_reg <= 16'd0;
            f_reg <= 16'd0;
            tau_zero_reg <= 1'b0;
            endpoint_zero_reg <= 1'b0;
            index_reg <= 8'd0;
            fraction_reg <= 7'd0;
            decay_reg <= 16'd0;
            y0_reg <= 16'd0;
            y1_reg <= 16'd0;
            delta_reg <= 17'd0;
            base_reg <= 32'd0;
            fraction_pipe_reg <= 7'd0;
            scaled_delta_reg <= 32'd0;
            base_pipe_reg <= 32'd0;
            busy <= 1'b0;
            done <= 1'b0;
            error <= 1'b0;
            fidelity_unorm16 <= 16'd0;
        end else begin
            done <= 1'b0;
            if (!busy) begin
                if (start) begin
                    x_reg <= x_uq4_12;
                    f_reg <= f_initial_unorm16;
                    tau_zero_reg <= tau_zero;
                    busy <= 1'b1;
                    stage <= 3'd0;
                end
            end else begin
                case (stage)
                    3'd0: begin
                        endpoint_zero_reg <= (x_reg >= 16'h8000);
                        index_reg <= x_reg[14:7];
                        fraction_reg <= x_reg[6:0];
                        stage <= 3'd1;
                    end
                    3'd1: begin
                        y0_reg <= exp_lut_a[index_reg];
                        if (index_reg == 8'hFF)
                            y1_reg <= exp_lut_b[index_reg];
                        else
                            y1_reg <= exp_lut_b[index_reg + 1'b1];
                        stage <= 3'd2;
                    end
                    3'd2: begin
                        delta_reg <= {1'b0, y0_reg} - {1'b0, y1_reg};
                        base_reg <= {9'd0, y0_reg, 7'd0};
                        fraction_pipe_reg <= fraction_reg;
                        stage <= 3'd3;
                    end
                    3'd3: begin
                        scaled_delta_reg <= delta_reg * {25'd0, fraction_pipe_reg};
                        base_pipe_reg <= base_reg;
                        stage <= 3'd4;
                    end
                    3'd4: begin
                        if (tau_zero_reg || endpoint_zero_reg) begin
                            decay_reg <= 16'd0;
                        end else begin
                            interpolation_tmp = base_pipe_reg - scaled_delta_reg;
                            rounded_tmp = (interpolation_tmp + 32'd64) >> 7;
                            if (rounded_tmp > 65535)
                                decay_reg <= 16'hFFFF;
                            else
                                decay_reg <= rounded_tmp[15:0];
                        end
                        stage <= 3'd5;
                    end
                    default: begin
                        product_tmp = {16'd0, f_reg} * {16'd0, decay_reg};
                        if (tau_zero_reg || endpoint_zero_reg)
                            fidelity_unorm16 <= 16'd0;
                        else
                            fidelity_unorm16 <= product_tmp[31:16];
                        error <= tau_zero_reg;
                        busy <= 1'b0;
                        done <= 1'b1;
                        stage <= 3'd0;
                    end
                endcase
            end
        end
    end

endmodule
