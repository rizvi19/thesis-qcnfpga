#!/usr/bin/env python3
"""
Generate a control-path stress testbench for the QFlow cloud-FPGA kernel.

Hardcore Local Check Step 3 focuses on transaction control rather than new
arithmetic cases: reset, start pulse handling, done pulse width, back-to-back
transactions, status flags, and stable latency-cycle reporting.

Input:
  vectors/golden_vectors.csv  (created by Step 2 or Step 1)

Output:
  tb/tb_qflow_control_stress.v
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VEC = ROOT / "vectors" / "golden_vectors.csv"
TB_OUT = ROOT / "tb" / "tb_qflow_control_stress.v"

if not VEC.exists():
    raise SystemExit(f"Missing {VEC}. Run Step 2 first or generate golden vectors before Step 3.")

rows = list(csv.DictReader(VEC.open()))
if not rows:
    raise SystemExit("golden_vectors.csv has no rows")

# Use all rows for the transaction-control pass. This intentionally reuses the
# same 215-vector dataset after Step 2, but checks stricter control properties.
CONTROL_ROWS = rows
BACK_TO_BACK_ROWS = rows[:min(32, len(rows))]


def split_ints(s: str, sep: str = "|") -> list[int]:
    return [int(x) for x in s.split(sep) if x != ""]


def split_paths(s: str) -> list[list[int]]:
    return [[int(x) for x in p.split("-")] for p in s.split("|")]


def emit_apply_vector(r: dict, indent: str = "        ") -> list[str]:
    out: list[str] = []
    out.append(f'{indent}// apply {r["test_id"]}')
    out.append(f"{indent}clear_inputs();")
    out.append(f"{indent}src_node = 6'd{int(r['src_node'])};")
    out.append(f"{indent}dst_node = 6'd{int(r['dst_node'])};")
    out.append(f"{indent}time_now = 32'd{int(r['time_now'])};")
    out.append(f"{indent}f_min_threshold = 16'd{int(r['f_min_q016'])};")
    fields = [
        ("set_edge_key_count", split_ints(r["key_counts"])),
        ("set_edge_finit", split_ints(r["f_init_q016"])),
        ("set_edge_decay", split_ints(r["decay_idx"])),
        ("set_edge_arrival", split_ints(r["arrival_rate_q8_8"])),
        ("set_edge_qber", split_ints(r["qber_q016"])),
        ("set_edge_distance", split_ints(r["distance_cost_q16_16"])),
    ]
    for task, vals in fields:
        for e, val in enumerate(vals):
            out.append(f"{indent}{task}({e}, {val});")
    for c, p in enumerate(split_paths(r["candidate_paths"])):
        for k, edge_id in enumerate(p):
            out.append(f"{indent}set_cand_edge({c}, {k}, {edge_id});")
    for c, ln in enumerate(split_ints(r["candidate_lens"])):
        out.append(f"{indent}set_cand_len({c}, {ln});")
    return out


body_control: list[str] = []
for r in CONTROL_ROWS:
    body_control.extend(emit_apply_vector(r))
    body_control.append(
        f'        run_pulse_and_check("{r["test_id"]}", '
        f'{int(r["expected_selected_path_id"])}, {int(r["expected_best_weight"])}, '
        f'{int(r["expected_bottleneck_fidelity"])}, {int(r["expected_valid_path"])});'
    )
    body_control.append("")

body_back_to_back: list[str] = []
for r in BACK_TO_BACK_ROWS:
    body_back_to_back.extend(emit_apply_vector(r))
    body_back_to_back.append(
        f'        run_back_to_back_check("BTB_{r["test_id"]}", '
        f'{int(r["expected_selected_path_id"])}, {int(r["expected_best_weight"])}, '
        f'{int(r["expected_bottleneck_fidelity"])}, {int(r["expected_valid_path"])});'
    )
    body_back_to_back.append("")

first = CONTROL_ROWS[0]
first_apply = "\n".join(emit_apply_vector(first))

content = f'''`timescale 1ns/1ps

module tb_qflow_control_stress;
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
    integer total_checks;
    integer control_csv;

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

    task record_failure(input [8*96-1:0] msg);
        begin
            failures = failures + 1;
            $display("FAIL_CONTROL: %0s", msg);
        end
    endtask

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

    task check_reset_outputs(input [8*64-1:0] label);
        begin
            total_checks = total_checks + 1;
            if (done !== 1'b0 || valid_path !== 1'b0 || no_path !== 1'b0 ||
                selected_path_id !== 2'd0 || best_weight !== 32'd0 ||
                bottleneck_fidelity !== 16'd0 || latency_cycles !== 32'd0) begin
                record_failure(label);
            end else begin
                $display("PASS_CONTROL %0s", label);
            end
        end
    endtask

    task run_pulse_and_check(
        input [8*64-1:0] test_id,
        input integer exp_path_id,
        input integer exp_weight,
        input integer exp_bottleneck,
        input integer exp_valid
    );
        begin
            total_checks = total_checks + 1;
            @(posedge clk);
            start <= 1'b1;
            @(posedge clk);
            start <= 1'b0;
            wait(done == 1'b1);
            #1;

            $fwrite(control_csv, "%0s,pulse,%0d,%0d,%0d,%0d,%0d,%0d\\n",
                    test_id, selected_path_id, best_weight, bottleneck_fidelity,
                    latency_cycles, {{29'd0, no_path, valid_path, done}}, exp_valid);

            if (selected_path_id !== exp_path_id[1:0] || best_weight !== exp_weight[31:0] ||
                bottleneck_fidelity !== exp_bottleneck[15:0] || valid_path !== exp_valid[0] ||
                latency_cycles !== 32'd2 || done !== 1'b1) begin
                $display("FAIL_CONTROL %0s: pulse output mismatch path=%0d weight=%0d bottleneck=%0d valid=%0d latency=%0d done=%0d",
                         test_id, selected_path_id, best_weight, bottleneck_fidelity, valid_path, latency_cycles, done);
                failures = failures + 1;
            end else begin
                $display("PASS_CONTROL %0s: pulse path=%0d latency=%0d", test_id, selected_path_id, latency_cycles);
            end

            @(posedge clk);
            #1;
            if (done !== 1'b0) begin
                $display("FAIL_CONTROL %0s: done did not deassert after one cycle", test_id);
                failures = failures + 1;
            end
        end
    endtask

    task run_back_to_back_check(
        input [8*80-1:0] test_id,
        input integer exp_path_id,
        input integer exp_weight,
        input integer exp_bottleneck,
        input integer exp_valid
    );
        begin
            // Same transaction as run_pulse_and_check, but intentionally no extra
            // idle gap is inserted between calls beyond the done-deassert check.
            run_pulse_and_check(test_id, exp_path_id, exp_weight, exp_bottleneck, exp_valid);
        end
    endtask

    task check_start_during_reset_ignored;
        begin
            total_checks = total_checks + 1;
            clear_inputs();
            start = 1'b1;
            rst_n = 1'b0;
            repeat (3) @(posedge clk);
            #1;
            if (done !== 1'b0 || latency_cycles !== 32'd0 || valid_path !== 1'b0 || no_path !== 1'b0) begin
                record_failure("start during reset not ignored");
            end else begin
                $display("PASS_CONTROL start_during_reset_ignored");
            end
            start = 1'b0;
            repeat (2) @(posedge clk);
            rst_n = 1'b1;
            repeat (2) @(posedge clk);
        end
    endtask

    task check_reset_mid_transaction;
        begin
            total_checks = total_checks + 1;
            clear_inputs();
{first_apply}
            @(posedge clk);
            start <= 1'b1;
            @(negedge clk);
            rst_n <= 1'b0;
            start <= 1'b0;
            @(posedge clk);
            #1;
            if (done !== 1'b0 || latency_cycles !== 32'd0 || valid_path !== 1'b0 || no_path !== 1'b0) begin
                record_failure("reset mid transaction did not clear outputs");
            end else begin
                $display("PASS_CONTROL reset_mid_transaction_clears_outputs");
            end
            @(posedge clk);
            rst_n <= 1'b1;
            repeat (2) @(posedge clk);
        end
    endtask

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        start = 1'b0;
        failures = 0;
        total_checks = 0;
        clear_inputs();
        control_csv = $fopen("results/control_stress_output.csv", "w");
        $fwrite(control_csv, "test_id,mode,selected_path_id,best_weight,bottleneck_fidelity,latency_cycles,status_flags,expected_valid_path\\n");

        repeat (4) @(posedge clk);
        #1;
        check_reset_outputs("reset_outputs_zero");
        check_start_during_reset_ignored();
        check_reset_mid_transaction();

        // Full pulse-control pass over all vectors.
{chr(10).join(body_control)}

        // Back-to-back subset pass. This ensures repeated host-style starts work
        // without carrying stale done/latency/status state between transactions.
{chr(10).join(body_back_to_back)}

        $fclose(control_csv);
        if (failures == 0) begin
            $display("CONTROL STRESS PASS: total_checks=%0d", total_checks);
        end else begin
            $display("CONTROL STRESS FAILED: failures=%0d total_checks=%0d", failures, total_checks);
        end
        $finish;
    end
endmodule
'''

TB_OUT.write_text(content)
print(TB_OUT)
print(f"Control rows: {len(CONTROL_ROWS)}")
print(f"Back-to-back rows: {len(BACK_TO_BACK_ROWS)}")
