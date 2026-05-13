#!/usr/bin/env python3
"""Generate a local MMIO/register-map testbench from golden_vectors.csv."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "vectors" / "golden_vectors.csv"
TB_OUT = ROOT / "tb" / "tb_qflow_mmio_regs.v"

NUM_EDGES = 8
NUM_CAND = 4
MAX_PATH_EDGES = 4

REG_CONTROL = 0x000
REG_STATUS = 0x004
REG_SRC_NODE = 0x010
REG_DST_NODE = 0x014
REG_TIME_NOW = 0x018
REG_F_MIN = 0x01C
EDGE_BASE = 0x100
EDGE_STRIDE = 0x020
EDGE_KEY_COUNT = 0x000
EDGE_F_INIT = 0x004
EDGE_DECAY_IDX = 0x008
EDGE_ARRIVAL = 0x00C
EDGE_QBER = 0x010
EDGE_DISTANCE = 0x014
CAND_BASE = 0x300
CAND_STRIDE = 0x010
CAND_EDGES = 0x000
CAND_LEN = 0x004
REG_SELECTED_ID = 0x400
REG_BEST_WEIGHT = 0x404
REG_BOTTLENECK = 0x408
REG_LATENCY = 0x40C


def parse_list(s: str) -> list[int]:
    return [int(x) for x in s.strip().split("|") if x != ""]


def parse_paths(s: str) -> list[list[int]]:
    paths = []
    for raw in s.strip().split("|"):
        vals = [int(x) for x in raw.split("-") if x != ""]
        vals = (vals + [0] * MAX_PATH_EDGES)[:MAX_PATH_EDGES]
        paths.append(vals)
    while len(paths) < NUM_CAND:
        paths.append([0] * MAX_PATH_EDGES)
    return paths[:NUM_CAND]


def pack_candidate_edges(edges: list[int]) -> int:
    packed = 0
    for idx, val in enumerate(edges[:MAX_PATH_EDGES]):
        packed |= (val & 0xF) << (idx * 4)
    return packed


def vstr(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def main() -> None:
    with GOLDEN.open(newline="") as f:
        rows = list(csv.DictReader(f))

    lines: list[str] = []
    ap = lines.append
    ap("`timescale 1ns/1ps")
    ap("module tb_qflow_mmio_regs;")
    ap("    reg clk;")
    ap("    reg rst_n;")
    ap("    reg wr_en;")
    ap("    reg rd_en;")
    ap("    reg [11:0] addr;")
    ap("    reg [31:0] wdata;")
    ap("    wire [31:0] rdata;")
    ap("    wire kernel_done_pulse;")
    ap("    wire status_done;")
    ap("    wire status_valid_path;")
    ap("    wire status_no_path;")
    ap("    wire status_busy;")
    ap("    integer fd;")
    ap("    integer fail_count;")
    ap("    integer tx_count;")
    ap("    reg [31:0] rd_status;")
    ap("    reg [31:0] rd_selected;")
    ap("    reg [31:0] rd_weight;")
    ap("    reg [31:0] rd_bottleneck;")
    ap("    reg [31:0] rd_latency;")
    ap("")
    ap("    qflow_mmio_regs dut (")
    ap("        .clk(clk), .rst_n(rst_n), .wr_en(wr_en), .rd_en(rd_en),")
    ap("        .addr(addr), .wdata(wdata), .rdata(rdata),")
    ap("        .kernel_done_pulse(kernel_done_pulse),")
    ap("        .status_done(status_done), .status_valid_path(status_valid_path),")
    ap("        .status_no_path(status_no_path), .status_busy(status_busy)")
    ap("    );")
    ap("")
    ap("    initial clk = 1'b0;")
    ap("    always #5 clk = ~clk;")
    ap("")
    ap("    task mmio_write;")
    ap("        input [11:0] a;")
    ap("        input [31:0] d;")
    ap("        begin")
    ap("            @(posedge clk);")
    ap("            addr <= a; wdata <= d; wr_en <= 1'b1; rd_en <= 1'b0;")
    ap("            @(posedge clk);")
    ap("            wr_en <= 1'b0; addr <= 12'd0; wdata <= 32'd0;")
    ap("        end")
    ap("    endtask")
    ap("")
    ap("    task mmio_read;")
    ap("        input [11:0] a;")
    ap("        output [31:0] d;")
    ap("        begin")
    ap("            @(posedge clk);")
    ap("            addr <= a; rd_en <= 1'b1; wr_en <= 1'b0;")
    ap("            #1 d = rdata;")
    ap("            @(posedge clk);")
    ap("            rd_en <= 1'b0; addr <= 12'd0;")
    ap("        end")
    ap("    endtask")
    ap("")
    ap("    task wait_done;")
    ap("        integer guard;")
    ap("        begin")
    ap("            guard = 0;")
    ap("            mmio_read(12'h004, rd_status);")
    ap("            while ((rd_status[0] !== 1'b1) && guard < 20) begin")
    ap("                guard = guard + 1;")
    ap("                mmio_read(12'h004, rd_status);")
    ap("            end")
    ap("            if (rd_status[0] !== 1'b1) begin")
    ap("                $display(\"FAIL_MMIO wait_done timeout status=%0h\", rd_status);")
    ap("                fail_count = fail_count + 1;")
    ap("            end")
    ap("        end")
    ap("    endtask")
    ap("")
    ap("    task run_case;")
    ap("        input [1023:0] test_id;")
    ap("        input integer exp_path;")
    ap("        input integer exp_weight;")
    ap("        input integer exp_bottleneck;")
    ap("        input integer exp_valid;")
    ap("        input integer exp_src;")
    ap("        input integer exp_dst;")
    ap("        begin")
    ap("            mmio_write(12'h000, 32'h0000_0001);")
    ap("            wait_done();")
    ap("            mmio_read(12'h400, rd_selected);")
    ap("            mmio_read(12'h404, rd_weight);")
    ap("            mmio_read(12'h408, rd_bottleneck);")
    ap("            mmio_read(12'h40C, rd_latency);")
    ap("            if ((rd_selected[1:0] !== exp_path[1:0]) || (rd_weight !== exp_weight[31:0]) ||")
    ap("                (rd_bottleneck[15:0] !== exp_bottleneck[15:0]) ||")
    ap("                (rd_status[1] !== exp_valid[0]) || (rd_status[2] !== ~exp_valid[0])) begin")
    ap("                $display(\"FAIL_MMIO %0s: path=%0d/%0d weight=%0d/%0d bottleneck=%0d/%0d status=%0h\",")
    ap("                         test_id, rd_selected[1:0], exp_path, rd_weight, exp_weight, rd_bottleneck[15:0], exp_bottleneck, rd_status);")
    ap("                fail_count = fail_count + 1;")
    ap("            end else begin")
    ap("                $display(\"PASS_MMIO %0s: path=%0d weight=%0d bottleneck=%0d latency=%0d status=%0h\",")
    ap("                         test_id, rd_selected[1:0], rd_weight, rd_bottleneck[15:0], rd_latency, rd_status);")
    ap("            end")
    ap("            $fwrite(fd, \"%0s,%0d,%0d,%0d,%0d,%0d,%0d,%0d\\n\",")
    ap("                    test_id, rd_selected[1:0], rd_weight, rd_bottleneck[15:0], rd_latency, rd_status, exp_src, exp_dst);")
    ap("            tx_count = tx_count + 1;")
    ap("        end")
    ap("    endtask")
    ap("")
    ap("    initial begin")
    ap("        wr_en = 1'b0; rd_en = 1'b0; addr = 12'd0; wdata = 32'd0;")
    ap("        rst_n = 1'b0; fail_count = 0; tx_count = 0;")
    ap("        fd = $fopen(\"results/mmio_output.csv\", \"w\");")
    ap("        $fwrite(fd, \"test_id,selected_path_id,best_weight,bottleneck_fidelity,latency_cycles,status_flags,src_node,dst_node\\n\");")
    ap("        repeat (5) @(posedge clk);")
    ap("        rst_n = 1'b1;")
    ap("        repeat (2) @(posedge clk);")
    ap("        mmio_read(12'h004, rd_status);")
    ap("        if (rd_status !== 32'd0) begin")
    ap("            $display(\"FAIL_MMIO reset_status_nonzero status=%0h\", rd_status);")
    ap("            fail_count = fail_count + 1;")
    ap("        end else begin")
    ap("            $display(\"PASS_MMIO reset_status_zero\");")
    ap("        end")
    ap("")

    for row in rows:
        test_id = vstr(row["test_id"])
        src = int(row["src_node"])
        dst = int(row["dst_node"])
        time_now = int(row["time_now"])
        f_min = int(row["f_min_q016"])
        key_counts = parse_list(row["key_counts"])
        f_init = parse_list(row["f_init_q016"])
        decay = parse_list(row["decay_idx"])
        arrival = parse_list(row["arrival_rate_q8_8"])
        qber = parse_list(row["qber_q016"])
        dist = parse_list(row["distance_cost_q16_16"])
        paths = parse_paths(row["candidate_paths"])
        lens = parse_list(row["candidate_lens"])
        exp_path = int(row["expected_selected_path_id"])
        exp_weight = int(row["expected_best_weight"])
        exp_bot = int(row["expected_bottleneck_fidelity"])
        exp_valid = int(row["expected_valid_path"])

        ap(f"        // {test_id}")
        ap("        mmio_write(12'h000, 32'h0000_0002); // soft reset sticky status")
        ap(f"        mmio_write(12'h010, 32'd{src});")
        ap(f"        mmio_write(12'h014, 32'd{dst});")
        ap(f"        mmio_write(12'h018, 32'd{time_now});")
        ap(f"        mmio_write(12'h01C, 32'd{f_min});")
        for i in range(NUM_EDGES):
            ap(f"        mmio_write(12'h{EDGE_BASE + i*EDGE_STRIDE + EDGE_KEY_COUNT:03X}, 32'd{key_counts[i]});")
            ap(f"        mmio_write(12'h{EDGE_BASE + i*EDGE_STRIDE + EDGE_F_INIT:03X}, 32'd{f_init[i]});")
            ap(f"        mmio_write(12'h{EDGE_BASE + i*EDGE_STRIDE + EDGE_DECAY_IDX:03X}, 32'd{decay[i]});")
            ap(f"        mmio_write(12'h{EDGE_BASE + i*EDGE_STRIDE + EDGE_ARRIVAL:03X}, 32'd{arrival[i]});")
            ap(f"        mmio_write(12'h{EDGE_BASE + i*EDGE_STRIDE + EDGE_QBER:03X}, 32'd{qber[i]});")
            ap(f"        mmio_write(12'h{EDGE_BASE + i*EDGE_STRIDE + EDGE_DISTANCE:03X}, 32'd{dist[i]});")
        for c in range(NUM_CAND):
            packed = pack_candidate_edges(paths[c])
            clen = lens[c] if c < len(lens) else 0
            ap(f"        mmio_write(12'h{CAND_BASE + c*CAND_STRIDE + CAND_EDGES:03X}, 32'h{packed:08X});")
            ap(f"        mmio_write(12'h{CAND_BASE + c*CAND_STRIDE + CAND_LEN:03X}, 32'd{clen});")
        ap(f"        run_case(\"{test_id}\", {exp_path}, {exp_weight}, {exp_bot}, {exp_valid}, {src}, {dst});")
        ap("")

    ap("        $fclose(fd);")
    ap("        if (fail_count == 0) begin")
    ap("            $display(\"MMIO WRAPPER PASS: transactions=%0d\", tx_count);")
    ap("        end else begin")
    ap("            $display(\"MMIO WRAPPER FAIL: transactions=%0d fail_count=%0d\", tx_count, fail_count);")
    ap("        end")
    ap("        $finish;")
    ap("    end")
    ap("endmodule")

    TB_OUT.parent.mkdir(parents=True, exist_ok=True)
    TB_OUT.write_text("\n".join(lines) + "\n")
    print(TB_OUT)
    print(f"MMIO vectors emitted: {len(rows)}")


if __name__ == "__main__":
    main()
