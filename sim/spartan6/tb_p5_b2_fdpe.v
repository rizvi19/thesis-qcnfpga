`timescale 1ns / 1ps

module tb_p5_b2_fdpe;
    parameter MAX_VECTORS = 1024;
    reg clk;
    reg rst;
    reg start;
    reg tau_zero;
    reg [15:0] x_uq4_12;
    reg [15:0] f_initial_unorm16;
    wire ready;
    wire busy;
    wire done;
    wire error;
    wire [15:0] fidelity_unorm16;
    reg [49:0] vectors [0:MAX_VECTORS-1];
    integer vector_count;
    integer index;
    integer failures;
    integer accept_cycle;
    integer cycle_count;
    reg [49:0] current;
    reg [1023:0] vectors_file;

    p5_b2_fdpe #(.LUT_FILE("rtl/spartan6/p5_b2_exp_lut.mem")) dut (
        .clk(clk), .rst(rst), .start(start), .tau_zero(tau_zero),
        .x_uq4_12(x_uq4_12), .f_initial_unorm16(f_initial_unorm16),
        .ready(ready), .busy(busy), .done(done), .error(error),
        .fidelity_unorm16(fidelity_unorm16)
    );

    always #5 clk = ~clk;
    always @(posedge clk) cycle_count = cycle_count + 1;

    initial begin
        clk = 1'b0;
        rst = 1'b1;
        start = 1'b0;
        tau_zero = 1'b0;
        x_uq4_12 = 16'd0;
        f_initial_unorm16 = 16'd0;
        failures = 0;
        cycle_count = 0;
        if (!$value$plusargs("VECTORS=%s", vectors_file))
            vectors_file = "sim/spartan6/p5_b2_fdpe_vectors.mem";
        if (!$value$plusargs("COUNT=%d", vector_count))
            vector_count = 519;
        $readmemh(vectors_file, vectors);

        repeat (2) @(posedge clk);
        #1;
        if (ready !== 1'b1 || busy !== 1'b0 || done !== 1'b0 ||
            error !== 1'b0 || fidelity_unorm16 !== 16'd0)
            $fatal(1, "P5_B2_RESET=FAIL");
        rst = 1'b0;

        for (index = 0; index < vector_count; index = index + 1) begin
            current = vectors[index];
            @(negedge clk);
            while (!ready) @(negedge clk);
            tau_zero = current[49];
            x_uq4_12 = current[47:32];
            f_initial_unorm16 = current[31:16];
            start = 1'b1;
            @(posedge clk);
            #1;
            accept_cycle = cycle_count;
            @(negedge clk);
            start = 1'b0;
            while (!done) begin
                @(posedge clk);
                #1;
            end
            if ((cycle_count - accept_cycle) != 6) begin
                $display("LATENCY_FAIL case=%0d got=%0d", index, cycle_count-accept_cycle);
                failures = failures + 1;
            end
            if (fidelity_unorm16 !== current[15:0] || error !== current[48]) begin
                $display("VALUE_FAIL case=%0d x=%h f=%h expected=%h/%b actual=%h/%b",
                    index, current[47:32], current[31:16], current[15:0],
                    current[48], fidelity_unorm16, error);
                failures = failures + 1;
            end
            @(negedge clk);
        end

        if (failures != 0)
            $fatal(1, "P5_B2_FDPE_SIM=FAIL count=%0d", failures);
        $display("P5_B2_FDPE_RESET=PASS");
        $display("P5_B2_FDPE_LATENCY=6_CYCLES_EXACT_PASS");
        $display("P5_B2_FDPE_VECTORS=%0d_OF_%0d_EXACT_PASS", vector_count, vector_count);
        $display("P5_B2_FDPE_SIM=PASS");
        $finish;
    end
endmodule
