module ga_controller (
    input  wire clk,
    input  wire rst_n,
    input  wire start_i,
    input  wire batch_done_i,
    output reg  clear_elite_o,
    output reg  result_valid_o
);
    reg running_r;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            running_r       <= 1'b0;
            clear_elite_o   <= 1'b0;
            result_valid_o  <= 1'b0;
        end else begin
            clear_elite_o  <= 1'b0;
            result_valid_o <= 1'b0;
            if (start_i) begin
                running_r     <= 1'b1;
                clear_elite_o <= 1'b1;
            end else if (running_r && batch_done_i) begin
                running_r      <= 1'b0;
                result_valid_o <= 1'b1;
            end
        end
    end
endmodule
