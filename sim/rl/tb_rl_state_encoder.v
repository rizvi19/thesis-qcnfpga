`timescale 1ns / 1ps

module tb_rl_state_encoder;
    reg         clk;
    reg         rst;
    reg         en;
    reg  [15:0] min_key_occupancy_u16;
    reg  [15:0] bottleneck_fidelity_u16;
    reg  [15:0] offered_request_load_u16;
    reg  [15:0] utilization_imbalance_u16;
    wire        valid;
    wire [7:0]  state_id;

    integer vector_file;
    integer scan_count;
    integer vector_count;
    integer failure_count;
    integer case_id_i;
    integer rst_i;
    integer en_i;
    integer key_i;
    integer fidelity_i;
    integer load_i;
    integer imbalance_i;
    integer expected_valid_i;
    integer expected_state_id_i;

    rl_state_encoder dut (
        .clk(clk),
        .rst(rst),
        .en(en),
        .min_key_occupancy_u16(min_key_occupancy_u16),
        .bottleneck_fidelity_u16(bottleneck_fidelity_u16),
        .offered_request_load_u16(offered_request_load_u16),
        .utilization_imbalance_u16(utilization_imbalance_u16),
        .valid(valid),
        .state_id(state_id)
    );

    always #5 clk = ~clk;

    initial begin
        clk = 1'b0;
        rst = 1'b0;
        en = 1'b0;
        min_key_occupancy_u16 = 16'd0;
        bottleneck_fidelity_u16 = 16'd0;
        offered_request_load_u16 = 16'd0;
        utilization_imbalance_u16 = 16'd0;
        vector_count = 0;
        failure_count = 0;

        vector_file = $fopen("sim/rl/p4_state_encoder_vectors.txt", "r");
        if (vector_file == 0) begin
            $display("P4_STATE_ENCODER_RTL_FAIL cannot_open_vector_file");
            $finish;
        end

        scan_count = $fscanf(
            vector_file,
            "%d %d %d %d %d %d %d %d %d\n",
            case_id_i,
            rst_i,
            en_i,
            key_i,
            fidelity_i,
            load_i,
            imbalance_i,
            expected_valid_i,
            expected_state_id_i
        );

        while (scan_count == 9) begin
            @(negedge clk);
            rst = rst_i[0];
            en = en_i[0];
            min_key_occupancy_u16 = key_i[15:0];
            bottleneck_fidelity_u16 = fidelity_i[15:0];
            offered_request_load_u16 = load_i[15:0];
            utilization_imbalance_u16 = imbalance_i[15:0];

            @(posedge clk);
            #1;
            if ((valid !== expected_valid_i[0]) ||
                (state_id !== expected_state_id_i[7:0])) begin
                failure_count = failure_count + 1;
                $display(
                    "P4_STATE_ENCODER_MISMATCH case=%0d valid=%0d expected_valid=%0d state=%0d expected_state=%0d",
                    case_id_i,
                    valid,
                    expected_valid_i,
                    state_id,
                    expected_state_id_i
                );
            end
            vector_count = vector_count + 1;

            scan_count = $fscanf(
                vector_file,
                "%d %d %d %d %d %d %d %d %d\n",
                case_id_i,
                rst_i,
                en_i,
                key_i,
                fidelity_i,
                load_i,
                imbalance_i,
                expected_valid_i,
                expected_state_id_i
            );
        end

        $fclose(vector_file);
        if (scan_count != -1) begin
            $display("P4_STATE_ENCODER_RTL_FAIL malformed_vector_file scan_count=%0d", scan_count);
            $finish;
        end
        if (vector_count != 297) begin
            $display("P4_STATE_ENCODER_RTL_FAIL vector_count=%0d expected=297", vector_count);
            $finish;
        end
        if (failure_count != 0) begin
            $display("P4_STATE_ENCODER_RTL_FAIL mismatches=%0d", failure_count);
            $finish;
        end

        $display("P4_STATE_ENCODER_RTL_PASS vectors=%0d mismatches=0", vector_count);
        $finish;
    end
endmodule
