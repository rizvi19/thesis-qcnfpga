`timescale 1ns / 1ps

module tb_p5_b3_skag;
    reg clk;
    reg rst;
    reg start;
    reg [63:0] edge_entry;
    reg [17:0] profile_payload;
    wire ready;
    wire busy;
    wire done;
    wire feasible;
    wire [31:0] weight;
    reg [114:0] vectors [0:1055];
    integer index;
    integer cycles;

    p5_b3_skag dut (
        .clk(clk), .rst(rst), .start(start), .edge_entry(edge_entry),
        .profile_payload(profile_payload), .ready(ready), .busy(busy),
        .done(done), .feasible(feasible), .weight_uq16_16(weight)
    );

    always #5 clk = ~clk;

    initial begin
        clk = 1'b0;
        rst = 1'b1;
        start = 1'b0;
        edge_entry = 64'd0;
        profile_payload = 18'd0;
        $readmemh("sim/spartan6/p5_b3_skag_vectors.mem", vectors);
        repeat (3) @(posedge clk);
        rst = 1'b0;
        for (index = 0; index < 1056; index = index + 1) begin
            while (!ready) @(posedge clk);
            edge_entry = vectors[index][114:51];
            profile_payload = vectors[index][50:33];
            start = 1'b1;
            @(posedge clk);
            start = 1'b0;
            cycles = 0;
            while (!done && cycles < 230) begin
                @(posedge clk);
                cycles = cycles + 1;
            end
            if (!done) begin
                $display("P5_B3_SKAG_TIMEOUT case=%0d", index);
                $fatal(1, "P5_B3_SKAG_SIM=TIMEOUT");
            end
            if ((weight !== vectors[index][32:1]) ||
                (feasible !== vectors[index][0])) begin
                $display("P5_B3_SKAG_MISMATCH case=%0d got=%08x/%0d expected=%08x/%0d",
                         index, weight, feasible, vectors[index][32:1], vectors[index][0]);
                $fatal(1, "P5_B3_SKAG_SIM=VALUE_FAIL");
            end
            @(posedge clk);
        end
        $display("P5_B3_SKAG_VECTORS=1056_OF_1056_EXACT_PASS");
        $finish;
    end
endmodule
