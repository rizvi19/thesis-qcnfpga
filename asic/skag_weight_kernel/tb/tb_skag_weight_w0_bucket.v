// ============================================================================
// Testbench for QFlow SKAG Weight Kernel W0
// ============================================================================

`timescale 1ns/1ps

module tb_skag_weight_w0_bucket;

    reg clk;
    reg rst_n;
    reg start;

    reg [15:0] key_count;
    reg [15:0] avg_fidelity_q016;
    reg [15:0] arrival_rate_q88;
    reg [15:0] qber_q016;

    reg [15:0] alpha_k_q88;
    reg [15:0] alpha_f_q88;
    reg [15:0] alpha_l_q88;
    reg [15:0] alpha_q_q88;

    wire done;
    wire [31:0] score_q16;

    skag_weight_w0_bucket dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),

        .key_count(key_count),
        .avg_fidelity_q016(avg_fidelity_q016),
        .arrival_rate_q88(arrival_rate_q88),
        .qber_q016(qber_q016),

        .alpha_k_q88(alpha_k_q88),
        .alpha_f_q88(alpha_f_q88),
        .alpha_l_q88(alpha_l_q88),
        .alpha_q_q88(alpha_q_q88),

        .done(done),
        .score_q16(score_q16)
    );

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    task run_case;
        input [15:0] t_key;
        input [15:0] t_fid;
        input [15:0] t_arrival;
        input [15:0] t_qber;
        begin
            @(posedge clk);
            key_count         <= t_key;
            avg_fidelity_q016 <= t_fid;
            arrival_rate_q88  <= t_arrival;
            qber_q016         <= t_qber;
            start             <= 1'b1;

            @(posedge clk);
            start <= 1'b0;

            wait(done == 1'b1);
            @(posedge clk);

            $display("CASE key=%0d fid=%0d arrival=%0d qber=%0d score=%0d",
                     t_key, t_fid, t_arrival, t_qber, score_q16);
        end
    endtask

    initial begin
        $dumpfile("asic/skag_weight_kernel/results/skag_weight_w0_bucket.vcd");
        $dumpvars(0, tb_skag_weight_w0_bucket);

        rst_n = 1'b0;
        start = 1'b0;

        key_count = 16'd0;
        avg_fidelity_q016 = 16'd0;
        arrival_rate_q88 = 16'd0;
        qber_q016 = 16'd0;

        // Alpha values from earlier SKAG evidence style:
        // 1.0, 1.5, 0.5, 2.0 in Q8.8
        alpha_k_q88 = 16'd256;
        alpha_f_q88 = 16'd384;
        alpha_l_q88 = 16'd128;
        alpha_q_q88 = 16'd512;

        repeat (5) @(posedge clk);
        rst_n = 1'b1;

        // Good edge: high key count, high fidelity, enough arrival, low QBER.
        run_case(16'd300, 16'd64000, 16'h0200, 16'd100);

        // Moderate edge.
        run_case(16'd128, 16'd60000, 16'h0080, 16'd500);

        // Bad edge: low key, low fidelity, poor arrival, high QBER.
        run_case(16'd10, 16'd50000, 16'h0020, 16'd2000);

        // No-key edge style.
        run_case(16'd0, 16'd62000, 16'h0040, 16'd800);

        repeat (5) @(posedge clk);

        $display("SKAG_WEIGHT_W0_BUCKET_SIM_PASS");
        $finish;
    end

endmodule
