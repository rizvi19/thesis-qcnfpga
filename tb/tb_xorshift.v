`timescale 1ns/1ps

module tb_xorshift;
    localparam integer N_SAMPLES = 10000;

    reg         clk;
    reg         rst_n;
    reg         seed_valid;
    reg  [63:0] seed0;
    reg  [63:0] seed1;
    reg         enable;
    wire [63:0] rand_o;
    wire        valid_o;
    wire        seeded_o;

    integer fh;
    integer sample_count;
    integer cycle_count;
    reg [63:0] prev0, prev1, prev2, prev3;
    reg [1023:0] dump_file;
    reg [1023:0] summary_file;

    xorshift128plus dut (
        .clk(clk),
        .rst_n(rst_n),
        .seed_valid_i(seed_valid),
        .seed0_i(seed0),
        .seed1_i(seed1),
        .enable_i(enable),
        .rand_o(rand_o),
        .valid_o(valid_o),
        .seeded_o(seeded_o)
    );

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    initial begin
        if (!$value$plusargs("DUMP=%s", dump_file))
            dump_file = "results/phase3/xorshift_dump.txt";
        if (!$value$plusargs("SUMMARY=%s", summary_file))
            summary_file = "results/phase3/xorshift_tb_summary.txt";

        $display("[TB_XORSHIFT] dump=%0s", dump_file);
        $display("[TB_XORSHIFT] summary=%0s", summary_file);

        rst_n = 1'b0;
        seed_valid = 1'b0;
        seed0 = 64'h0123_4567_89AB_CDEF;
        seed1 = 64'hF0E1_D2C3_B4A5_9687;
        enable = 1'b0;
        sample_count = 0;
        cycle_count = 0;
        prev0 = 64'd0;
        prev1 = 64'd0;
        prev2 = 64'd0;
        prev3 = 64'd0;

        #25;
        rst_n = 1'b1;

        @(posedge clk);
        seed_valid <= 1'b1;
        @(posedge clk);
        seed_valid <= 1'b0;
        enable <= 1'b1;

        fh = $fopen(dump_file, "w");
        if (fh == 0) begin
            $fatal(1, "[TB_XORSHIFT] Could not open dump file: %0s", dump_file);
        end
        $fwrite(fh, "index,value_hex,value_dec\n");

        while (sample_count < N_SAMPLES) begin
            @(posedge clk);
            cycle_count = cycle_count + 1;
            if (valid_o) begin
                // Catch trivial very-short cycles early so the TB cannot report a false pass.
                if ((sample_count >= 4) &&
                    (rand_o == prev0) &&
                    (prev0 == prev1) && (prev1 == prev2) && (prev2 == prev3)) begin
                    $fatal(1, "[TB_XORSHIFT] Constant-output failure detected.");
                end
                if ((sample_count >= 4) &&
                    (rand_o == prev3) && (prev0 == prev2) && (prev1 == prev3) && (prev0 != prev1)) begin
                    $fatal(1, "[TB_XORSHIFT] Short repeating cycle detected (period 2 or 4).");
                end

                $fwrite(fh, "%0d,%016h,%0d\n", sample_count, rand_o, rand_o);
                prev3 = prev2;
                prev2 = prev1;
                prev1 = prev0;
                prev0 = rand_o;
                sample_count = sample_count + 1;
            end
            if (cycle_count > (N_SAMPLES + 50)) begin
                $fatal(1, "[TB_XORSHIFT] Timeout before collecting all samples.");
            end
        end

        $fclose(fh);

        fh = $fopen(summary_file, "w");
        if (fh != 0) begin
            $fwrite(fh, "XORSHIFT testbench summary\n");
            $fwrite(fh, "samples=%0d\n", sample_count);
            $fwrite(fh, "cycles=%0d\n", cycle_count);
            $fwrite(fh, "seed0=%016h\n", seed0);
            $fwrite(fh, "seed1=%016h\n", seed1);
            $fclose(fh);
        end

        $display("[TB_XORSHIFT] PASS: samples=%0d cycles=%0d", sample_count, cycle_count);
        $finish;
    end
endmodule
