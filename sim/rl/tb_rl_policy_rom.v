`timescale 1ns / 1ps

module tb_rl_policy_rom;
    reg        clk;
    reg        rst;
    reg        en;
    reg  [7:0] state_id;
    wire       valid;
    wire [1:0] proposed_action;

    integer vector_file;
    integer scan_count;
    integer vector_count;
    integer failure_count;
    integer case_id_i;
    integer rst_i;
    integer en_i;
    integer state_id_i;
    integer expected_valid_i;
    integer expected_action_i;

    rl_policy_rom dut (
        .clk(clk),
        .rst(rst),
        .en(en),
        .state_id(state_id),
        .valid(valid),
        .proposed_action(proposed_action)
    );

    always #5 clk = ~clk;

    initial begin
        clk = 1'b0;
        rst = 1'b0;
        en = 1'b0;
        state_id = 8'd0;
        vector_count = 0;
        failure_count = 0;

        vector_file = $fopen("sim/rl/p4_policy_rom_vectors.txt", "r");
        if (vector_file == 0) begin
            $display("P4_POLICY_ROM_RTL_FAIL cannot_open_vector_file");
            $finish;
        end

        scan_count = $fscanf(
            vector_file,
            "%d %d %d %d %d %d\n",
            case_id_i,
            rst_i,
            en_i,
            state_id_i,
            expected_valid_i,
            expected_action_i
        );

        while (scan_count == 6) begin
            @(negedge clk);
            rst = rst_i[0];
            en = en_i[0];
            state_id = state_id_i[7:0];

            @(posedge clk);
            #1;
            if ((valid !== expected_valid_i[0]) ||
                (proposed_action !== expected_action_i[1:0])) begin
                failure_count = failure_count + 1;
                $display(
                    "P4_POLICY_ROM_MISMATCH case=%0d valid=%0d expected_valid=%0d action=%0d expected_action=%0d",
                    case_id_i,
                    valid,
                    expected_valid_i,
                    proposed_action,
                    expected_action_i
                );
            end
            vector_count = vector_count + 1;

            scan_count = $fscanf(
                vector_file,
                "%d %d %d %d %d %d\n",
                case_id_i,
                rst_i,
                en_i,
                state_id_i,
                expected_valid_i,
                expected_action_i
            );
        end

        $fclose(vector_file);
        if (scan_count != -1) begin
            $display("P4_POLICY_ROM_RTL_FAIL malformed_vector_file scan_count=%0d", scan_count);
            $finish;
        end
        if (vector_count != 260) begin
            $display("P4_POLICY_ROM_RTL_FAIL vector_count=%0d expected=260", vector_count);
            $finish;
        end
        if (failure_count != 0) begin
            $display("P4_POLICY_ROM_RTL_FAIL mismatches=%0d", failure_count);
            $finish;
        end

        $display("P4_POLICY_ROM_RTL_PASS vectors=%0d mismatches=0", vector_count);
        $finish;
    end
endmodule
