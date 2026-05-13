#!/usr/bin/env python3
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader((ROOT/'vectors/golden_vectors.csv').open()))


def split_ints(s, sep='|'):
    return [int(x) for x in s.split(sep) if x != '']


def split_paths(s):
    return [[int(x) for x in p.split('-')] for p in s.split('|')]

body = []
for idx, r in enumerate(rows, 1):
    body.append(f'        // {r["test_id"]}')
    body.append('        clear_inputs();')
    body.append(f'        src_node = 6\'d{int(r["src_node"])};')
    body.append(f'        dst_node = 6\'d{int(r["dst_node"])};')
    body.append(f'        time_now = 32\'d{int(r["time_now"])};')
    body.append(f'        f_min_threshold = 16\'d{int(r["f_min_q016"])};')
    fields = [
        ('set_edge_key_count', split_ints(r['key_counts'])),
        ('set_edge_finit', split_ints(r['f_init_q016'])),
        ('set_edge_decay', split_ints(r['decay_idx'])),
        ('set_edge_arrival', split_ints(r['arrival_rate_q8_8'])),
        ('set_edge_qber', split_ints(r['qber_q016'])),
        ('set_edge_distance', split_ints(r['distance_cost_q16_16'])),
    ]
    for task, vals in fields:
        for e, val in enumerate(vals):
            body.append(f'        {task}({e}, {val});')
    for c, p in enumerate(split_paths(r['candidate_paths'])):
        for k, edge_id in enumerate(p):
            body.append(f'        set_cand_edge({c}, {k}, {edge_id});')
    for c, ln in enumerate(split_ints(r['candidate_lens'])):
        body.append(f'        set_cand_len({c}, {ln});')
    body.append(f'        run_and_check("{r["test_id"]}", {int(r["expected_selected_path_id"])}, {int(r["expected_best_weight"])}, {int(r["expected_bottleneck_fidelity"])}, {int(r["expected_valid_path"])});')
    body.append('')

content = f'''`timescale 1ns/1ps

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
            key_counts_flat = {{(NUM_EDGES*16){{1'b0}}}};
            f_init_flat = {{(NUM_EDGES*FID_W){{1'b0}}}};
            decay_idx_flat = {{(NUM_EDGES*8){{1'b0}}}};
            arrival_rate_flat = {{(NUM_EDGES*16){{1'b0}}}};
            qber_flat = {{(NUM_EDGES*FID_W){{1'b0}}}};
            distance_cost_flat = {{(NUM_EDGES*SCORE_W){{1'b0}}}};
            cand_edges_flat = {{(NUM_CAND*MAX_PATH_EDGES*EDGE_ID_W){{1'b0}}}};
            cand_lens_flat = {{(NUM_CAND*3){{1'b0}}}};
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

            $fwrite(hw_csv, "%0s,%0d,%0d,%0d,%0d,%0d,%0d,%0d\\n",
                    test_id, selected_path_id, best_weight, bottleneck_fidelity,
                    latency_cycles, {{29'd0, no_path, valid_path, done}}, src_node, dst_node);

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
        $fwrite(hw_csv, "test_id,selected_path_id,best_weight,bottleneck_fidelity,latency_cycles,status_flags,src_node,dst_node\\n");

        repeat (3) @(posedge clk);
        rst_n = 1'b1;

{chr(10).join(body)}

        $fclose(hw_csv);
        if (failures == 0) begin
            $display("ALL TESTS PASS");
        end else begin
            $display("TESTS FAILED: %0d failure(s)", failures);
        end
        $finish;
    end
endmodule
'''

(ROOT/'tb/tb_qflow_cloud_kernel.v').write_text(content)
print(ROOT/'tb/tb_qflow_cloud_kernel.v')
