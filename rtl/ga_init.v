`timescale 1ns/1ps

module ga_init #(
    parameter integer POP_MAX = 64,
    parameter integer INDEX_W = 6
) (
    input  wire                clk,
    input  wire                rst_n,
    input  wire                start_i,
    input  wire                ready_i,
    input  wire [INDEX_W-1:0]  pop_size_i,
    output reg                 req_valid_o,
    output reg  [INDEX_W-1:0]  req_index_o,
    output reg                 issue_done_o
);
    reg active_r;

    initial begin
        if (POP_MAX <= 0)
            $error("ga_init POP_MAX must be positive");
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            active_r      <= 1'b0;
            req_valid_o   <= 1'b0;
            req_index_o   <= {INDEX_W{1'b0}};
            issue_done_o  <= 1'b0;
        end else begin
            issue_done_o <= 1'b0;
            if (start_i) begin
                active_r    <= 1'b1;
                req_valid_o <= (pop_size_i != {INDEX_W{1'b0}});
                req_index_o <= {INDEX_W{1'b0}};
            end else if (active_r && ready_i) begin
                if (req_index_o + {{(INDEX_W-1){1'b0}},1'b1} >= pop_size_i) begin
                    active_r     <= 1'b0;
                    req_valid_o  <= 1'b0;
                    issue_done_o <= 1'b1;
                end else begin
                    req_valid_o <= 1'b1;
                    req_index_o <= req_index_o + {{(INDEX_W-1){1'b0}},1'b1};
                end
            end else begin
                req_valid_o <= 1'b0;
            end
        end
    end
endmodule
