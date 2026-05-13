`timescale 1ns/1ps

module tb_qflow_cloud_kernel;
    localparam NUM_EDGES      = 8;
    localparam NUM_CAND       = 4;
    localparam MAX_PATH_EDGES = 4;
    localparam EDGE_ID_W      = 4;
    localparam FID_W          = 16;
    localparam SCORE_W        = 32;

    reg clk;
    reg rst_n;
    reg start;
    reg [5:0] src_node;
    reg [5:0] dst_node;
    reg [31:0] time_now;
    reg [FID_W-1:0] f_min_threshold;

    reg [NUM_EDGES*16-1:0] key_counts_flat;
    reg [NUM_EDGES*FID_W-1:0] f_init_flat;
    reg [NUM_EDGES*8-1:0] decay_idx_flat;
    reg [NUM_EDGES*16-1:0] arrival_rate_flat;
    reg [NUM_EDGES*FID_W-1:0] qber_flat;
    reg [NUM_EDGES*SCORE_W-1:0] distance_cost_flat;
    reg [NUM_CAND*MAX_PATH_EDGES*EDGE_ID_W-1:0] cand_edges_flat;
    reg [NUM_CAND*3-1:0] cand_lens_flat;

    wire done;
    wire valid_path;
    wire no_path;
    wire [1:0] selected_path_id;
    wire [SCORE_W-1:0] best_weight;
    wire [FID_W-1:0] bottleneck_fidelity;
    wire [31:0] latency_cycles;

    integer failures;
    integer hw_csv;

    qflow_cloud_kernel dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .src_node(src_node),
        .dst_node(dst_node),
        .time_now(time_now),
        .f_min_threshold(f_min_threshold),
        .key_counts_flat(key_counts_flat),
        .f_init_flat(f_init_flat),
        .decay_idx_flat(decay_idx_flat),
        .arrival_rate_flat(arrival_rate_flat),
        .qber_flat(qber_flat),
        .distance_cost_flat(distance_cost_flat),
        .cand_edges_flat(cand_edges_flat),
        .cand_lens_flat(cand_lens_flat),
        .done(done),
        .valid_path(valid_path),
        .no_path(no_path),
        .selected_path_id(selected_path_id),
        .best_weight(best_weight),
        .bottleneck_fidelity(bottleneck_fidelity),
        .latency_cycles(latency_cycles)
    );

    always #5 clk = ~clk;

    task clear_inputs;
        begin
            start = 1'b0;
            src_node = 6'd0;
            dst_node = 6'd0;
            time_now = 32'd0;
            f_min_threshold = 16'd0;
            key_counts_flat = {(NUM_EDGES*16){1'b0}};
            f_init_flat = {(NUM_EDGES*FID_W){1'b0}};
            decay_idx_flat = {(NUM_EDGES*8){1'b0}};
            arrival_rate_flat = {(NUM_EDGES*16){1'b0}};
            qber_flat = {(NUM_EDGES*FID_W){1'b0}};
            distance_cost_flat = {(NUM_EDGES*SCORE_W){1'b0}};
            cand_edges_flat = {(NUM_CAND*MAX_PATH_EDGES*EDGE_ID_W){1'b0}};
            cand_lens_flat = {(NUM_CAND*3){1'b0}};
        end
    endtask

    task set_edge_key_count(input integer edge_idx, input integer value);
        key_counts_flat[edge_idx*16 +: 16] = value[15:0];
    endtask

    task set_edge_finit(input integer edge_idx, input integer value);
        f_init_flat[edge_idx*FID_W +: FID_W] = value[15:0];
    endtask

    task set_edge_decay(input integer edge_idx, input integer value);
        decay_idx_flat[edge_idx*8 +: 8] = value[7:0];
    endtask

    task set_edge_arrival(input integer edge_idx, input integer value);
        arrival_rate_flat[edge_idx*16 +: 16] = value[15:0];
    endtask

    task set_edge_qber(input integer edge_idx, input integer value);
        qber_flat[edge_idx*FID_W +: FID_W] = value[15:0];
    endtask

    task set_edge_distance(input integer edge_idx, input integer value);
        distance_cost_flat[edge_idx*SCORE_W +: SCORE_W] = value[31:0];
    endtask

    task set_cand_edge(input integer cand, input integer pos, input integer edge_id);
        cand_edges_flat[(cand*MAX_PATH_EDGES + pos)*EDGE_ID_W +: EDGE_ID_W] = edge_id[EDGE_ID_W-1:0];
    endtask

    task set_cand_len(input integer cand, input integer len);
        cand_lens_flat[cand*3 +: 3] = len[2:0];
    endtask

    task run_and_check(
        input [8*64-1:0] test_id,
        input integer exp_path_id,
        input integer exp_weight,
        input integer exp_bottleneck,
        input integer exp_valid
    );
        begin
            @(posedge clk);
            start <= 1'b1;
            @(posedge clk);
            start <= 1'b0;
            wait(done == 1'b1);
            @(posedge clk);

            $fwrite(hw_csv, "%0s,%0d,%0d,%0d,%0d,%0d,%0d,%0d\n",
                    test_id, selected_path_id, best_weight, bottleneck_fidelity,
                    latency_cycles, {29'd0, no_path, valid_path, done}, src_node, dst_node);

            if (selected_path_id !== exp_path_id[1:0] || best_weight !== exp_weight[31:0] ||
                bottleneck_fidelity !== exp_bottleneck[15:0] || valid_path !== exp_valid[0]) begin
                $display("FAIL %0s: got path=%0d weight=%0d bottleneck=%0d valid=%0d | expected path=%0d weight=%0d bottleneck=%0d valid=%0d",
                         test_id, selected_path_id, best_weight, bottleneck_fidelity, valid_path,
                         exp_path_id, exp_weight, exp_bottleneck, exp_valid);
                failures = failures + 1;
            end else begin
                $display("PASS %0s: path=%0d weight=%0d bottleneck=%0d latency_cycles=%0d",
                         test_id, selected_path_id, best_weight, bottleneck_fidelity, latency_cycles);
            end
        end
    endtask

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        failures = 0;
        clear_inputs();
        hw_csv = $fopen("results/hardware_output.csv", "w");
        $fwrite(hw_csv, "test_id,selected_path_id,best_weight,bottleneck_fidelity,latency_cycles,status_flags,src_node,dst_node\n");

        repeat (3) @(posedge clk);
        rst_n = 1'b1;

        // T001_normal_ring6
        clear_inputs();
        src_node = 6'd0;
        dst_node = 6'd3;
        time_now = 32'd1000;
        f_min_threshold = 16'd55705;
        set_edge_key_count(0, 6);
        set_edge_key_count(1, 5);
        set_edge_key_count(2, 4);
        set_edge_key_count(3, 9);
        set_edge_key_count(4, 8);
        set_edge_key_count(5, 7);
        set_edge_key_count(6, 3);
        set_edge_key_count(7, 0);
        set_edge_finit(0, 63569);
        set_edge_finit(1, 62914);
        set_edge_finit(2, 64224);
        set_edge_finit(3, 64880);
        set_edge_finit(4, 64224);
        set_edge_finit(5, 63569);
        set_edge_finit(6, 64880);
        set_edge_finit(7, 64880);
        set_edge_decay(0, 1);
        set_edge_decay(1, 1);
        set_edge_decay(2, 2);
        set_edge_decay(3, 1);
        set_edge_decay(4, 1);
        set_edge_decay(5, 1);
        set_edge_decay(6, 3);
        set_edge_decay(7, 0);
        set_edge_arrival(0, 1200);
        set_edge_arrival(1, 1150);
        set_edge_arrival(2, 1000);
        set_edge_arrival(3, 1400);
        set_edge_arrival(4, 1300);
        set_edge_arrival(5, 1250);
        set_edge_arrival(6, 700);
        set_edge_arrival(7, 900);
        set_edge_qber(0, 1311);
        set_edge_qber(1, 1966);
        set_edge_qber(2, 1311);
        set_edge_qber(3, 655);
        set_edge_qber(4, 1311);
        set_edge_qber(5, 1311);
        set_edge_qber(6, 655);
        set_edge_qber(7, 655);
        set_edge_distance(0, 1310720);
        set_edge_distance(1, 1441792);
        set_edge_distance(2, 1245184);
        set_edge_distance(3, 1179648);
        set_edge_distance(4, 1179648);
        set_edge_distance(5, 1179648);
        set_edge_distance(6, 1638400);
        set_edge_distance(7, 655360);
        set_cand_edge(0, 0, 0);
        set_cand_edge(0, 1, 1);
        set_cand_edge(0, 2, 2);
        set_cand_edge(0, 3, 0);
        set_cand_edge(1, 0, 3);
        set_cand_edge(1, 1, 4);
        set_cand_edge(1, 2, 5);
        set_cand_edge(1, 3, 0);
        set_cand_edge(2, 0, 0);
        set_cand_edge(2, 1, 6);
        set_cand_edge(2, 2, 5);
        set_cand_edge(2, 3, 0);
        set_cand_edge(3, 0, 7);
        set_cand_edge(3, 1, 0);
        set_cand_edge(3, 2, 0);
        set_cand_edge(3, 3, 0);
        set_cand_len(0, 3);
        set_cand_len(1, 3);
        set_cand_len(2, 3);
        set_cand_len(3, 1);
        run_and_check("T001_normal_ring6", 1, 3665362, 61612, 1);

        // T002_blocked_candidate
        clear_inputs();
        src_node = 6'd0;
        dst_node = 6'd3;
        time_now = 32'd2000;
        f_min_threshold = 16'd56360;
        set_edge_key_count(0, 2);
        set_edge_key_count(1, 0);
        set_edge_key_count(2, 4);
        set_edge_key_count(3, 7);
        set_edge_key_count(4, 8);
        set_edge_key_count(5, 8);
        set_edge_key_count(6, 6);
        set_edge_key_count(7, 3);
        set_edge_finit(0, 62258);
        set_edge_finit(1, 62258);
        set_edge_finit(2, 64224);
        set_edge_finit(3, 64880);
        set_edge_finit(4, 64224);
        set_edge_finit(5, 63569);
        set_edge_finit(6, 62914);
        set_edge_finit(7, 64880);
        set_edge_decay(0, 2);
        set_edge_decay(1, 2);
        set_edge_decay(2, 1);
        set_edge_decay(3, 1);
        set_edge_decay(4, 1);
        set_edge_decay(5, 1);
        set_edge_decay(6, 4);
        set_edge_decay(7, 0);
        set_edge_arrival(0, 850);
        set_edge_arrival(1, 850);
        set_edge_arrival(2, 1100);
        set_edge_arrival(3, 1200);
        set_edge_arrival(4, 1250);
        set_edge_arrival(5, 1250);
        set_edge_arrival(6, 600);
        set_edge_arrival(7, 1300);
        set_edge_qber(0, 1966);
        set_edge_qber(1, 1966);
        set_edge_qber(2, 1311);
        set_edge_qber(3, 655);
        set_edge_qber(4, 1311);
        set_edge_qber(5, 1311);
        set_edge_qber(6, 1966);
        set_edge_qber(7, 655);
        set_edge_distance(0, 1376256);
        set_edge_distance(1, 1376256);
        set_edge_distance(2, 1441792);
        set_edge_distance(3, 1507328);
        set_edge_distance(4, 1507328);
        set_edge_distance(5, 1507328);
        set_edge_distance(6, 1310720);
        set_edge_distance(7, 1966080);
        set_cand_edge(0, 0, 0);
        set_cand_edge(0, 1, 1);
        set_cand_edge(0, 2, 2);
        set_cand_edge(0, 3, 0);
        set_cand_edge(1, 0, 3);
        set_cand_edge(1, 1, 4);
        set_cand_edge(1, 2, 5);
        set_cand_edge(1, 3, 0);
        set_cand_edge(2, 0, 0);
        set_cand_edge(2, 1, 6);
        set_cand_edge(2, 2, 5);
        set_cand_edge(2, 3, 0);
        set_cand_edge(3, 0, 7);
        set_cand_edge(3, 1, 0);
        set_cand_edge(3, 2, 0);
        set_cand_edge(3, 3, 0);
        set_cand_len(0, 3);
        set_cand_len(1, 3);
        set_cand_len(2, 3);
        set_cand_len(3, 1);
        run_and_check("T002_blocked_candidate", 3, 1997214, 64879, 1);

        // T003_high_threshold
        clear_inputs();
        src_node = 6'd0;
        dst_node = 6'd3;
        time_now = 32'd3000;
        f_min_threshold = 16'd60948;
        set_edge_key_count(0, 6);
        set_edge_key_count(1, 5);
        set_edge_key_count(2, 4);
        set_edge_key_count(3, 9);
        set_edge_key_count(4, 8);
        set_edge_key_count(5, 7);
        set_edge_key_count(6, 3);
        set_edge_key_count(7, 0);
        set_edge_finit(0, 63569);
        set_edge_finit(1, 62914);
        set_edge_finit(2, 64224);
        set_edge_finit(3, 64880);
        set_edge_finit(4, 64224);
        set_edge_finit(5, 63569);
        set_edge_finit(6, 64880);
        set_edge_finit(7, 64880);
        set_edge_decay(0, 3);
        set_edge_decay(1, 4);
        set_edge_decay(2, 4);
        set_edge_decay(3, 0);
        set_edge_decay(4, 0);
        set_edge_decay(5, 0);
        set_edge_decay(6, 5);
        set_edge_decay(7, 0);
        set_edge_arrival(0, 1200);
        set_edge_arrival(1, 1150);
        set_edge_arrival(2, 1000);
        set_edge_arrival(3, 1400);
        set_edge_arrival(4, 1300);
        set_edge_arrival(5, 1250);
        set_edge_arrival(6, 700);
        set_edge_arrival(7, 900);
        set_edge_qber(0, 1311);
        set_edge_qber(1, 1966);
        set_edge_qber(2, 1311);
        set_edge_qber(3, 655);
        set_edge_qber(4, 1311);
        set_edge_qber(5, 1311);
        set_edge_qber(6, 655);
        set_edge_qber(7, 655);
        set_edge_distance(0, 1310720);
        set_edge_distance(1, 1441792);
        set_edge_distance(2, 1245184);
        set_edge_distance(3, 1179648);
        set_edge_distance(4, 1179648);
        set_edge_distance(5, 1179648);
        set_edge_distance(6, 1638400);
        set_edge_distance(7, 655360);
        set_cand_edge(0, 0, 0);
        set_cand_edge(0, 1, 1);
        set_cand_edge(0, 2, 2);
        set_cand_edge(0, 3, 0);
        set_cand_edge(1, 0, 3);
        set_cand_edge(1, 1, 4);
        set_cand_edge(1, 2, 5);
        set_cand_edge(1, 3, 0);
        set_cand_edge(2, 0, 0);
        set_cand_edge(2, 1, 6);
        set_cand_edge(2, 2, 5);
        set_cand_edge(2, 3, 0);
        set_cand_edge(3, 0, 7);
        set_cand_edge(3, 1, 0);
        set_cand_edge(3, 2, 0);
        set_cand_edge(3, 3, 0);
        set_cand_len(0, 3);
        set_cand_len(1, 3);
        set_cand_len(2, 3);
        set_cand_len(3, 1);
        run_and_check("T003_high_threshold", 1, 3617938, 63568, 1);


        $fclose(hw_csv);
        if (failures == 0) begin
            $display("ALL TESTS PASS");
        end else begin
            $display("TESTS FAILED: %0d failure(s)", failures);
        end
        $finish;
    end
endmodule
