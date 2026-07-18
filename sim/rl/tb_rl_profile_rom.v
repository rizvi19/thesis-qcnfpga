`timescale 1ns / 1ps

module tb_rl_profile_rom;
    reg         clk;
    reg         rst;
    reg         en;
    reg  [1:0]  selected_action;
    wire        valid;
    wire [17:0] profile_payload;

    integer vector_file;
    integer scan_count;
    integer vector_count;
    integer failure_count;
    integer case_id_i;
    integer rst_i;
    integer en_i;
    integer action_i;
    integer expected_valid_i;
    integer expected_payload_i;

    rl_profile_rom dut (
        .clk(clk),
        .rst(rst),
        .en(en),
        .selected_action(selected_action),
        .valid(valid),
        .profile_payload(profile_payload)
    );

    always #5 clk = ~clk;

    initial begin
        clk = 1'b0;
        rst = 1'b0;
        en = 1'b0;
        selected_action = 2'd0;
        vector_count = 0;
        failure_count = 0;

        vector_file = $fopen("sim/rl/p4_profile_rom_vectors.txt", "r");
        if (vector_file == 0) begin
            $display("P4_PROFILE_ROM_RTL_FAIL cannot_open_vector_file");
            $finish;
        end

        scan_count = $fscanf(
            vector_file,
            "%d %d %d %d %d %d\n",
            case_id_i,
            rst_i,
            en_i,
            action_i,
            expected_valid_i,
            expected_payload_i
        );

        while (scan_count == 6) begin
            @(negedge clk);
            rst = rst_i[0];
            en = en_i[0];
            selected_action = action_i[1:0];

            @(posedge clk);
            #1;
            if ((valid !== expected_valid_i[0]) ||
                (profile_payload !== expected_payload_i[17:0])) begin
                failure_count = failure_count + 1;
                $display(
                    "P4_PROFILE_ROM_MISMATCH case=%0d valid=%0d expected_valid=%0d payload=%05h expected_payload=%05h",
                    case_id_i,
                    valid,
                    expected_valid_i,
                    profile_payload,
                    expected_payload_i[17:0]
                );
            end
            vector_count = vector_count + 1;

            scan_count = $fscanf(
                vector_file,
                "%d %d %d %d %d %d\n",
                case_id_i,
                rst_i,
                en_i,
                action_i,
                expected_valid_i,
                expected_payload_i
            );
        end

        $fclose(vector_file);
        if (scan_count != -1) begin
            $display("P4_PROFILE_ROM_RTL_FAIL malformed_vector_file scan_count=%0d", scan_count);
            $finish;
        end
        if (vector_count != 8) begin
            $display("P4_PROFILE_ROM_RTL_FAIL vector_count=%0d expected=8", vector_count);
            $finish;
        end
        if (failure_count != 0) begin
            $display("P4_PROFILE_ROM_RTL_FAIL mismatches=%0d", failure_count);
            $finish;
        end

        $display("P4_PROFILE_ROM_RTL_PASS vectors=%0d mismatches=0", vector_count);
        $finish;
    end
endmodule
