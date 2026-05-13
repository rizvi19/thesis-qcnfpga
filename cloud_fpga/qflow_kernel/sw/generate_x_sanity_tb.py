#!/usr/bin/env python3
"""
Generate an X/Z propagation and output-sanity testbench for the QFlow cloud-FPGA kernel.

Hardcore Local Check Step 4 focuses on simulation hygiene before AWS EC2 F2:
  - no unknown (X) or high-impedance (Z) on observable output ports after reset,
  - no X/Z after every host-style transaction,
  - done/valid/no_path status consistency,
  - output values remain equal to golden vectors,
  - idle state after done deassertion does not reintroduce X/Z.

Input:
  vectors/golden_vectors.csv

Output:
  tb/tb_qflow_x_sanity.v
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VEC = ROOT / "vectors" / "golden_vectors.csv"
TB_OUT = ROOT / "tb" / "tb_qflow_x_sanity.v"

if not VEC.exists():
    raise SystemExit(f"Missing {VEC}. Run Step 2 first to generate the 215-vector dataset.")

rows = list(csv.DictReader(VEC.open()))
if not rows:
    raise SystemExit("golden_vectors.csv has no rows")


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

body: list[str] = []
for r in rows:
    body.extend(emit_apply_vector(r))
    body.append(
        f'        run_x_sanity_transaction("{r["test_id"]}", '
        f'{int(r["expected_selected_path_id"])}, {int(r["expected_best_weight"])}, '
        f'{int(r["expected_bottleneck_fidelity"])}, {int(r["expected_valid_path"])});'
    )
    body.append("")

content = f'''`timescale 1ns/1ps

module tb_qflow_x_sanity;
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
    integer sanity_csv;

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

    function has_xz_1;
        input sig;
        begin
            has_xz_1 = (sig !== 1'b0 && sig !== 1'b1);
        end
    endfunction

    function has_xz_2;
        input [1:0] sig;
        begin
            has_xz_2 = (^sig === 1'bx);
        end
    endfunction

    function has_xz_16;
        input [15:0] sig;
        begin
            has_xz_16 = (^sig === 1'bx);
        end
    endfunction

    function has_xz_32;
        input [31:0] sig;
        begin
            has_xz_32 = (^sig === 1'bx);
        end
    endfunction

    task record_failure(input [8*128-1:0] msg);
        begin
            failures = failures + 1;
            $display("FAIL_X_SANITY: %0s", msg);
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

    task check_no_xz_outputs(input [8*96-1:0] label);
        begin
            total_checks = total_checks + 1;
            if (has_xz_1(done) || has_xz_1(valid_path) || has_xz_1(no_path) ||
                has_xz_2(selected_path_id) || has_xz_32(best_weight) ||
                has_xz_16(bottleneck_fidelity) || has_xz_32(latency_cycles)) begin
                $display("FAIL_X_SANITY %0s: X/Z detected done=%b valid=%b no_path=%b path=%b weight=%b bottleneck=%b latency=%b",
                         label, done, valid_path, no_path, selected_path_id, best_weight, bottleneck_fidelity, latency_cycles);
                failures = failures + 1;
            end
        end
    endtask

    task check_status_consistency(input [8*96-1:0] label, input integer exp_valid);
        begin
            total_checks = total_checks + 1;
            if (done !== 1'b1) begin
                $display("FAIL_X_SANITY %0s: done not asserted at transaction completion", label);
                failures = failures + 1;
            end
            if (exp_valid == 1) begin
                if (valid_path !== 1'b1 || no_path !== 1'b0) begin
                    $display("FAIL_X_SANITY %0s: valid/no_path inconsistent for expected-valid case valid=%b no_path=%b", label, valid_path, no_path);
                    failures = failures + 1;
                end
            end else begin
                if (valid_path !== 1'b0 || no_path !== 1'b1) begin
                    $display("FAIL_X_SANITY %0s: valid/no_path inconsistent for expected-no-path case valid=%b no_path=%b", label, valid_path, no_path);
                    failures = failures + 1;
                end
            end
        end
    endtask

    task run_x_sanity_transaction(
        input [8*96-1:0] test_id,
        input integer exp_path_id,
        input integer exp_weight,
        input integer exp_bottleneck,
        input integer exp_valid
    );
        begin
            @(posedge clk);
            #1;
            check_no_xz_outputs({{test_id, "_idle_before"}});

            start <= 1'b1;
            @(posedge clk);
            #1;
            check_no_xz_outputs({{test_id, "_after_start"}});
            start <= 1'b0;

            wait(done == 1'b1);
            #1;
            check_no_xz_outputs({{test_id, "_done"}});
            check_status_consistency(test_id, exp_valid);

            $fwrite(sanity_csv, "%0s,%0d,%0d,%0d,%0d,%0d,%0d\\n",
                    test_id, selected_path_id, best_weight, bottleneck_fidelity,
                    latency_cycles, {{29'd0, no_path, valid_path, done}}, exp_valid);

            if (selected_path_id !== exp_path_id[1:0] || best_weight !== exp_weight[31:0] ||
                bottleneck_fidelity !== exp_bottleneck[15:0] || valid_path !== exp_valid[0] ||
                latency_cycles !== 32'd2) begin
                $display("FAIL_X_SANITY %0s: value mismatch path=%0d weight=%0d bottleneck=%0d valid=%0d latency=%0d",
                         test_id, selected_path_id, best_weight, bottleneck_fidelity, valid_path, latency_cycles);
                failures = failures + 1;
            end else begin
                $display("PASS_X_SANITY %0s: no_xz path=%0d latency=%0d", test_id, selected_path_id, latency_cycles);
            end

            @(posedge clk);
            #1;
            check_no_xz_outputs({{test_id, "_idle_after"}});
            if (done !== 1'b0) begin
                $display("FAIL_X_SANITY %0s: done did not deassert", test_id);
                failures = failures + 1;
            end
        end
    endtask

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        start = 1'b0;
        failures = 0;
        total_checks = 0;
        clear_inputs();
        sanity_csv = $fopen("results/x_sanity_output.csv", "w");
        $fwrite(sanity_csv, "test_id,selected_path_id,best_weight,bottleneck_fidelity,latency_cycles,status_flags,expected_valid_path\\n");

        // During reset, outputs should be driven and deterministic.
        repeat (4) @(posedge clk);
        #1;
        check_no_xz_outputs("reset_phase");
        if (done !== 1'b0 || valid_path !== 1'b0 || no_path !== 1'b0 ||
            selected_path_id !== 2'd0 || best_weight !== 32'd0 ||
            bottleneck_fidelity !== 16'd0 || latency_cycles !== 32'd0) begin
            record_failure("reset outputs are not clean zero values");
        end else begin
            $display("PASS_X_SANITY reset_outputs_driven_zero");
        end

        rst_n = 1'b1;
        repeat (2) @(posedge clk);
        #1;
        check_no_xz_outputs("post_reset_idle");

{chr(10).join(body)}

        $fclose(sanity_csv);
        if (failures == 0) begin
            $display("X SANITY PASS: total_checks=%0d", total_checks);
        end else begin
            $display("X SANITY FAILED: failures=%0d total_checks=%0d", failures, total_checks);
        end
        $finish;
    end
endmodule
'''

TB_OUT.write_text(content)
print(TB_OUT)
print(f"X-sanity rows: {len(rows)}")
