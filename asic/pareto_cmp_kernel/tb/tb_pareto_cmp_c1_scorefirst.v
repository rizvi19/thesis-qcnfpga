// ============================================================================
// Testbench for QFlow Pareto Comparator C1
// ============================================================================

`timescale 1ns/1ps

module tb_pareto_cmp_c1_scorefirst;

    reg clk;
    reg rst_n;
    reg start;

    reg [31:0] score_a;
    reg [15:0] fidelity_a;
    reg [15:0] key_count_a;
    reg [7:0]  hop_count_a;
    reg [15:0] qber_a;

    reg [31:0] score_b;
    reg [15:0] fidelity_b;
    reg [15:0] key_count_b;
    reg [7:0]  hop_count_b;
    reg [15:0] qber_b;

    wire done;
    wire select_a;
    wire select_b;
    wire tie;

    pareto_cmp_c1_scorefirst dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),

        .score_a(score_a),
        .fidelity_a(fidelity_a),
        .key_count_a(key_count_a),
        .hop_count_a(hop_count_a),
        .qber_a(qber_a),

        .score_b(score_b),
        .fidelity_b(fidelity_b),
        .key_count_b(key_count_b),
        .hop_count_b(hop_count_b),
        .qber_b(qber_b),

        .done(done),
        .select_a(select_a),
        .select_b(select_b),
        .tie(tie)
    );

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    task run_case;
        input [31:0] t_score_a;
        input [15:0] t_fidelity_a;
        input [15:0] t_key_count_a;
        input [7:0]  t_hop_count_a;
        input [15:0] t_qber_a;

        input [31:0] t_score_b;
        input [15:0] t_fidelity_b;
        input [15:0] t_key_count_b;
        input [7:0]  t_hop_count_b;
        input [15:0] t_qber_b;

        input [127:0] case_name;
        begin
            @(posedge clk);

            score_a      <= t_score_a;
            fidelity_a   <= t_fidelity_a;
            key_count_a  <= t_key_count_a;
            hop_count_a  <= t_hop_count_a;
            qber_a       <= t_qber_a;

            score_b      <= t_score_b;
            fidelity_b   <= t_fidelity_b;
            key_count_b  <= t_key_count_b;
            hop_count_b  <= t_hop_count_b;
            qber_b       <= t_qber_b;

            start <= 1'b1;

            @(posedge clk);
            start <= 1'b0;

            wait(done == 1'b1);
            @(posedge clk);

            $display("CASE %s select_a=%0d select_b=%0d tie=%0d",
                     case_name, select_a, select_b, tie);
        end
    endtask

    initial begin
        $dumpfile("asic/pareto_cmp_kernel/results/pareto_cmp_c1_scorefirst.vcd");
        $dumpvars(0, tb_pareto_cmp_c1_scorefirst);

        rst_n = 1'b0;
        start = 1'b0;

        score_a = 32'd0;
        fidelity_a = 16'd0;
        key_count_a = 16'd0;
        hop_count_a = 8'd0;
        qber_a = 16'd0;

        score_b = 32'd0;
        fidelity_b = 16'd0;
        key_count_b = 16'd0;
        hop_count_b = 8'd0;
        qber_b = 16'd0;

        repeat (5) @(posedge clk);
        rst_n = 1'b1;

        // A wins by score.
        run_case(
            32'd900,  16'd62000, 16'd200, 8'd5, 16'd300,
            32'd1000, 16'd65000, 16'd400, 8'd3, 16'd100,
            "A_SCORE"
        );

        // B wins by score.
        run_case(
            32'd1500, 16'd65000, 16'd400, 8'd3, 16'd100,
            32'd1000, 16'd62000, 16'd200, 8'd5, 16'd300,
            "B_SCORE"
        );

        // Equal score, A wins by fidelity.
        run_case(
            32'd1000, 16'd65000, 16'd200, 8'd5, 16'd300,
            32'd1000, 16'd62000, 16'd400, 8'd3, 16'd100,
            "A_FID"
        );

        // Equal score/fidelity, B wins by key count.
        run_case(
            32'd1000, 16'd64000, 16'd200, 8'd3, 16'd100,
            32'd1000, 16'd64000, 16'd400, 8'd5, 16'd300,
            "B_KEY"
        );

        // Equal until hop, A wins lower hop.
        run_case(
            32'd1000, 16'd64000, 16'd300, 8'd3, 16'd300,
            32'd1000, 16'd64000, 16'd300, 8'd5, 16'd100,
            "A_HOP"
        );

        // Equal until qber, B wins lower qber.
        run_case(
            32'd1000, 16'd64000, 16'd300, 8'd3, 16'd300,
            32'd1000, 16'd64000, 16'd300, 8'd3, 16'd100,
            "B_QBER"
        );

        // Exact tie.
        run_case(
            32'd1000, 16'd64000, 16'd300, 8'd3, 16'd100,
            32'd1000, 16'd64000, 16'd300, 8'd3, 16'd100,
            "TIE"
        );

        repeat (5) @(posedge clk);

        $display("PARETO_CMP_C1_SCOREFIRST_SIM_PASS");
        $finish;
    end

endmodule
