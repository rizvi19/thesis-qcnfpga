`timescale 1ns / 1ps

module p5_b3_skag (
    input  wire        clk,
    input  wire        rst,
    input  wire        start,
    input  wire [63:0] edge_entry,
    input  wire [17:0] profile_payload,
    output wire        ready,
    output reg         busy,
    output reg         done,
    output reg         feasible,
    output reg  [31:0] weight_uq16_16
);

    localparam [31:0] MAX_FINITE = 32'hFFFFFFFE;
    localparam [31:0] INFINITY = 32'hFFFFFFFF;

    reg [15:0] key_count;
    reg [15:0] fidelity;
    reg [15:0] key_rate;
    reg [15:0] qber;
    reg [2:0] alpha1;
    reg [2:0] alpha2;
    reg [2:0] alpha3;
    reg [2:0] alpha4;
    reg [2:0] state;
    reg [2:0] term_index;
    reg [31:0] sum_reg;
    reg div_start;
    reg [47:0] div_dividend;
    reg [17:0] div_divisor;
    wire div_ready;
    wire div_busy;
    wire div_done;
    wire [47:0] div_quotient;

    reg [18:0] product_tmp;
    reg [46:0] numerator_tmp;
    reg [16:0] denominator_tmp;
    reg [48:0] sum_tmp;

    function [18:0] multiply_u3_u16;
        input [2:0] coefficient;
        input [15:0] value;
        begin
            multiply_u3_u16 =
                (coefficient[0] ? {3'd0, value} : 19'd0) +
                (coefficient[1] ? {2'd0, value, 1'b0} : 19'd0) +
                (coefficient[2] ? {1'd0, value, 2'b00} : 19'd0);
        end
    endfunction

    assign ready = ~busy;

    p5_b3_iterative_divider u_divider (
        .clk(clk),
        .rst(rst),
        .start(div_start),
        .dividend(div_dividend),
        .divisor(div_divisor),
        .ready(div_ready),
        .busy(div_busy),
        .done(div_done),
        .quotient(div_quotient)
    );

    always @(posedge clk) begin
        if (rst) begin
            key_count <= 16'd0;
            fidelity <= 16'd0;
            key_rate <= 16'd0;
            qber <= 16'd0;
            alpha1 <= 3'd0;
            alpha2 <= 3'd0;
            alpha3 <= 3'd0;
            alpha4 <= 3'd0;
            state <= 3'd0;
            term_index <= 3'd0;
            sum_reg <= 32'd0;
            div_start <= 1'b0;
            div_dividend <= 48'd0;
            div_divisor <= 18'd1;
            busy <= 1'b0;
            done <= 1'b0;
            feasible <= 1'b0;
            weight_uq16_16 <= INFINITY;
        end else begin
            done <= 1'b0;
            div_start <= 1'b0;
            if (!busy) begin
                if (start) begin
                    key_count <= edge_entry[63:48];
                    fidelity <= edge_entry[47:32];
                    key_rate <= edge_entry[31:16];
                    qber <= edge_entry[15:0];
                    alpha1 <= profile_payload[17:15];
                    alpha2 <= profile_payload[14:12];
                    alpha3 <= profile_payload[11:9];
                    alpha4 <= profile_payload[8:6];
                    term_index <= 3'd0;
                    sum_reg <= 32'd0;
                    feasible <= 1'b0;
                    weight_uq16_16 <= INFINITY;
                    busy <= 1'b1;
                    state <= 3'd1;
                end
            end else begin
                case (state)
                    3'd1: begin
                        if ((key_count == 16'd0) || (fidelity == 16'd0) ||
                            (key_rate == 16'd0)) begin
                            feasible <= 1'b0;
                            weight_uq16_16 <= INFINITY;
                            state <= 3'd5;
                        end else begin
                            state <= 3'd2;
                        end
                    end
                    3'd2: begin
                        product_tmp = 19'd0;
                        numerator_tmp = 47'd0;
                        denominator_tmp = 17'd1;
                        case (term_index)
                            3'd0: begin
                                numerator_tmp = {28'd0, alpha1, 16'd0};
                                denominator_tmp = {key_count, 1'b0};
                            end
                            3'd1: begin
                                product_tmp = multiply_u3_u16(alpha2, 16'hFFFF);
                                numerator_tmp = {12'd0, product_tmp, 16'd0};
                                denominator_tmp = {fidelity, 1'b0};
                            end
                            3'd2: begin
                                numerator_tmp = {21'd0, alpha3, 23'd0};
                                denominator_tmp = {1'b0, key_rate};
                            end
                            default: begin
                                product_tmp = multiply_u3_u16(alpha4, qber);
                                numerator_tmp = {12'd0, product_tmp, 16'd0};
                                denominator_tmp = 17'd131070;
                            end
                        endcase
                        div_dividend <= ({1'b0, numerator_tmp} << 1) + denominator_tmp;
                        div_divisor <= {denominator_tmp, 1'b0};
                        state <= 3'd3;
                    end
                    3'd3: begin
                        if (div_ready) begin
                            div_start <= 1'b1;
                            state <= 3'd4;
                        end
                    end
                    3'd4: begin
                        if (div_done) begin
                            sum_tmp = {17'd0, sum_reg} + {1'b0, div_quotient};
                            if ((|div_quotient[47:32]) ||
                                (sum_tmp > {17'd0, MAX_FINITE}))
                                sum_reg <= MAX_FINITE;
                            else
                                sum_reg <= sum_tmp[31:0];
                            if (term_index == 3'd3) begin
                                feasible <= 1'b1;
                                if ((|div_quotient[47:32]) ||
                                    (sum_tmp > {17'd0, MAX_FINITE}))
                                    weight_uq16_16 <= MAX_FINITE;
                                else
                                    weight_uq16_16 <= sum_tmp[31:0];
                                state <= 3'd5;
                            end else begin
                                term_index <= term_index + 1'b1;
                                state <= 3'd2;
                            end
                        end
                    end
                    default: begin
                        busy <= 1'b0;
                        done <= 1'b1;
                        state <= 3'd0;
                    end
                endcase
            end
        end
    end

endmodule
