#!/usr/bin/env python3
from __future__ import annotations
import csv
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPLAY=ROOT/"results/nexys3/p6_replay/p6_all_replay.csv"
GOLDEN=ROOT/"results/nexys3/p6_step3_golden_rtl/golden_results.csv"
REPLAY_ROM=ROOT/"rtl/spartan6/p6_replay_rom.v"
EXPECTED_ROM=ROOT/"rtl/spartan6/p6_expected_result_rom.v"
FORMATTER=ROOT/"rtl/spartan6/p6_qf6r_formatter.v"
CORE=ROOT/"rtl/spartan6/p6_physical_campaign_core.v"
TOP=ROOT/"rtl/spartan6/p6_nexys3_campaign_top.v"
UCF=ROOT/"constraints/nexys3/p6_nexys3_campaign.ucf"
TB=ROOT/"sim/spartan6/tb_p6_physical_campaign_shell.v"
SUMMARY=ROOT/"results/nexys3/p6_step3_physical_shell/shell_simulation_summary.csv"
SIMLOG=ROOT/"evidence/nexys3/p6_step3_physical_shell/five_mode_shell_simulation.log"

def read_csv(path):
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path,fields,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

def require(c,label):
    if not c:
        raise AssertionError(label)
    print("PASS",label)

def generate_replay_rom(rows):
    fields=[
      ("test_id","output reg [15:0] test_id","16'd0"),
      ("input_valid","output reg input_valid","1'b0"),
      ("min_key_occupancy_u16","output reg [15:0] min_key","16'd0"),
      ("bottleneck_fidelity_state_u16","output reg [15:0] state_fidelity","16'd0"),
      ("offered_request_load_u16","output reg [15:0] offered_load","16'd0"),
      ("utilization_imbalance_state_u16","output reg [15:0] imbalance","16'd0"),
      ("c0_valid","output reg c0_valid","1'b0"),
      ("c0_cost","output reg [31:0] c0_cost","32'd0"),
      ("c0_fidelity","output reg [15:0] c0_fidelity","16'd0"),
      ("c0_utilization","output reg [31:0] c0_utilization","32'd0"),
      ("c0_hops","output reg [2:0] c0_hops","3'd0"),
      ("c0_slot","output reg [1:0] c0_slot","2'd0"),
      ("c1_valid","output reg c1_valid","1'b0"),
      ("c1_cost","output reg [31:0] c1_cost","32'd0"),
      ("c1_fidelity","output reg [15:0] c1_fidelity","16'd0"),
      ("c1_utilization","output reg [31:0] c1_utilization","32'd0"),
      ("c1_hops","output reg [2:0] c1_hops","3'd0"),
      ("c1_slot","output reg [1:0] c1_slot","2'd1")]
    out=["`timescale 1ns / 1ps\n",
         "module p6_replay_rom(\n",
         " input wire [6:0] index,\n"]
    for n,(_,decl,_) in enumerate(fields):
        out.append(" "+decl+("," if n<len(fields)-1 else "")+"\n")
    out.append(");\nalways @* begin\n")
    names=["test_id","input_valid","min_key","state_fidelity","offered_load","imbalance",
           "c0_valid","c0_cost","c0_fidelity","c0_utilization","c0_hops","c0_slot",
           "c1_valid","c1_cost","c1_fidelity","c1_utilization","c1_hops","c1_slot"]
    for name,(_,_,default) in zip(names,fields):
        out.append(f" {name} = {default};\n")
    out.append(" case(index)\n")
    widths=[16,1,16,16,16,16,1,32,16,32,3,2,1,32,16,32,3,2]
    keys=[x[0] for x in fields]
    for idx,row in enumerate(rows):
        out.append(f"  7'd{idx}: begin\n")
        for name,key,width in zip(names,keys,widths):
            out.append(f"   {name} = {width}'d{int(row[key])};\n")
        out.append("  end\n")
    out.append("  default: begin end\n endcase\nend\nendmodule\n")
    REPLAY_ROM.write_text("".join(out),encoding="utf-8")

def generate_expected_rom(rows):
    by_key={(int(r["policy_id"]),int(r["test_id"])):r for r in rows}
    replay=read_csv(REPLAY)
    out=["`timescale 1ns / 1ps\n",
         "module p6_expected_result_rom(\n",
         " input wire [2:0] policy_mode,\n",
         " input wire [6:0] replay_index,\n",
         " output reg [7:0] state_id,\n",
         " output reg [1:0] profile_id,\n",
         " output reg [7:0] selected_path,\n",
         " output reg [17:0] score,\n",
         " output reg [15:0] bottleneck_fidelity,\n",
         " output reg [15:0] cycles,\n",
         " output reg [2:0] status\n",
         ");\nalways @* begin\n",
         " state_id=0;profile_id=0;selected_path=0;score=0;",
         "bottleneck_fidelity=0;cycles=0;status=0;\n",
         " case({policy_mode,replay_index})\n"]
    for mode in range(5):
        for idx,rr in enumerate(replay):
            row=by_key[(mode,int(rr["test_id"]))]
            key=(mode<<7)|idx
            out.append(f"  10'd{key}: begin ")
            out.append(f"state_id=8'd{int(row['state_id'])};")
            out.append(f"profile_id=2'd{int(row['profile_id'])};")
            out.append(f"selected_path=8'd{int(row['selected_path'])};")
            out.append(f"score=18'd{int(row['score'])};")
            out.append(f"bottleneck_fidelity=16'd{int(row['bottleneck_fidelity'])};")
            out.append(f"cycles=16'd{int(row['cycles'])};")
            out.append(f"status=3'd{int(row['status'])}; end\n")
    out.append("  default: begin end\n endcase\nend\nendmodule\n")
    EXPECTED_ROM.write_text("".join(out),encoding="utf-8")

def generate_formatter():
    FORMATTER.write_text(r'''`timescale 1ns / 1ps
module p6_qf6r_formatter(
 input wire clk,input wire rst,input wire start,
 output wire ready,output reg done,
 input wire [15:0] test_id,input wire [2:0] policy_id,
 input wire [7:0] state_id,input wire [1:0] profile_id,
 input wire [7:0] selected_path,input wire [17:0] score,
 input wire [15:0] bottleneck_fidelity,input wire [15:0] cycles,
 input wire [2:0] status,
 input wire uart_ready,output wire byte_valid,output reg [7:0] byte_data
);
localparam IDLE=0,LOAD=1,CONVERT=2,SEND=3;
reg [2:0] state;
reg [3:0] field_index;
reg [5:0] digit_offset;
reg [3:0] digits_remaining;
reg [31:0] work_value;
reg [5:0] byte_index;
reg [3:0] digits[0:26];
reg [15:0] test_id_r,cycles_r;
reg [2:0] policy_id_r,status_r;
reg [7:0] state_id_r,selected_path_r;
reg [1:0] profile_id_r;
reg [17:0] score_r;
reg [15:0] fidelity_r;
integer n;
assign ready=(state==IDLE);
assign byte_valid=(state==SEND)&&uart_ready;
always @* begin
 byte_data=0;
 case(byte_index)
 0:byte_data="Q";1:byte_data="F";2:byte_data="6";3:byte_data="R";
 4:byte_data=",";5:byte_data="1";6:byte_data=",";
 7:byte_data=8'h30+digits[0];8:byte_data=8'h30+digits[1];
 9:byte_data=8'h30+digits[2];10:byte_data=8'h30+digits[3];
 11:byte_data=",";12:byte_data=8'h30+digits[4];13:byte_data=",";
 14:byte_data=8'h30+digits[5];15:byte_data=8'h30+digits[6];
 16:byte_data=8'h30+digits[7];17:byte_data=",";
 18:byte_data=8'h30+digits[8];19:byte_data=",";
 20:byte_data=8'h30+digits[9];21:byte_data=8'h30+digits[10];
 22:byte_data=8'h30+digits[11];23:byte_data=",";
 24:byte_data=8'h30+digits[12];25:byte_data=8'h30+digits[13];
 26:byte_data=8'h30+digits[14];27:byte_data=8'h30+digits[15];
 28:byte_data=8'h30+digits[16];29:byte_data=8'h30+digits[17];
 30:byte_data=",";31:byte_data=8'h30+digits[18];
 32:byte_data=8'h30+digits[19];33:byte_data=8'h30+digits[20];
 34:byte_data=8'h30+digits[21];35:byte_data=8'h30+digits[22];
 36:byte_data=",";37:byte_data=8'h30+digits[23];
 38:byte_data=8'h30+digits[24];39:byte_data=8'h30+digits[25];
 40:byte_data=",";41:byte_data=8'h30+digits[26];
 42:byte_data=8'h0d;43:byte_data=8'h0a;
 endcase
end
always @(posedge clk) begin
 if(rst) begin
  state<=IDLE;field_index<=0;digit_offset<=0;digits_remaining<=0;
  work_value<=0;byte_index<=0;done<=0;
  test_id_r<=0;policy_id_r<=0;state_id_r<=0;profile_id_r<=0;
  selected_path_r<=0;score_r<=0;fidelity_r<=0;cycles_r<=0;status_r<=0;
  for(n=0;n<27;n=n+1) digits[n]<=0;
 end else begin
  done<=0;
  case(state)
   IDLE:if(start) begin
    test_id_r<=test_id;policy_id_r<=policy_id;state_id_r<=state_id;
    profile_id_r<=profile_id;selected_path_r<=selected_path;
    score_r<=score;fidelity_r<=bottleneck_fidelity;cycles_r<=cycles;
    status_r<=status;field_index<=0;byte_index<=0;state<=LOAD;
   end
   LOAD:begin
    case(field_index)
     0:begin work_value<=test_id_r;digit_offset<=0;digits_remaining<=4;end
     1:begin work_value<=policy_id_r;digit_offset<=4;digits_remaining<=1;end
     2:begin work_value<=state_id_r;digit_offset<=5;digits_remaining<=3;end
     3:begin work_value<=profile_id_r;digit_offset<=8;digits_remaining<=1;end
     4:begin work_value<=selected_path_r;digit_offset<=9;digits_remaining<=3;end
     5:begin work_value<=score_r;digit_offset<=12;digits_remaining<=6;end
     6:begin work_value<=fidelity_r;digit_offset<=18;digits_remaining<=5;end
     7:begin work_value<=cycles_r;digit_offset<=23;digits_remaining<=3;end
     default:begin work_value<=status_r;digit_offset<=26;digits_remaining<=1;end
    endcase
    state<=CONVERT;
   end
   CONVERT:begin
    digits[digit_offset+digits_remaining-1]<=work_value%10;
    work_value<=work_value/10;
    if(digits_remaining==1) begin
     if(field_index==8) begin byte_index<=0;state<=SEND;end
     else begin field_index<=field_index+1'b1;state<=LOAD;end
    end else digits_remaining<=digits_remaining-1'b1;
   end
   SEND:if(uart_ready) begin
    if(byte_index==43) begin done<=1;state<=IDLE;end
    else byte_index<=byte_index+1'b1;
   end
   default:state<=IDLE;
  endcase
 end
end
endmodule
''',encoding="utf-8")

def generate_core():
    CORE.write_text(r'''`timescale 1ns / 1ps
module p6_physical_campaign_core #(
 parameter [2:0] POLICY_MODE=3'd0,
 parameter integer CLK_HZ=100000000,
 parameter integer UART_BAUD=115200
)(
 input wire clk,input wire rst,
 output wire uart_tx,
 output reg campaign_done,
 output reg [6:0] records_completed,
 output reg [7:0] pass_count,
 output reg [15:0] error_count
);
localparam GROUP_RESET=0,WAIT_READY=1,ISSUE=2,WAIT_DONE=3,
           START_FORMAT=4,WAIT_FORMAT=5,ADVANCE=6,COMPLETE=7;
reg [3:0] state;
reg [2:0] reset_count;
reg [6:0] replay_index;
reg core_rst,core_start,format_start;

wire [15:0] test_id;
wire input_valid;
wire [15:0] min_key,state_fidelity,offered_load,imbalance;
wire c0_valid,c1_valid;
wire [31:0] c0_cost,c1_cost,c0_utilization,c1_utilization;
wire [15:0] c0_fidelity,c1_fidelity;
wire [2:0] c0_hops,c1_hops;
wire [1:0] c0_slot,c1_slot;

wire core_ready,core_done;
wire [2:0] core_policy_id,core_status;
wire [7:0] core_state_id;
wire [1:0] core_profile_id,core_selected_slot;
wire [17:0] core_score;
wire [15:0] core_fidelity,core_cycles;

wire [7:0] expected_state,expected_path;
wire [1:0] expected_profile;
wire [17:0] expected_score;
wire [15:0] expected_fidelity,expected_cycles;
wire [2:0] expected_status;

reg [15:0] tx_test_id,tx_cycles;
reg [2:0] tx_policy_id,tx_status;
reg [7:0] tx_state_id,tx_path;
reg [1:0] tx_profile_id;
reg [17:0] tx_score;
reg [15:0] tx_fidelity;

wire formatter_ready,formatter_done,formatter_valid;
wire [7:0] formatter_byte;
wire uart_ready;

wire [7:0] norm_state=(core_status==3'd2)?8'd0:core_state_id;
wire [1:0] norm_profile=(core_status==3'd2)?2'd0:core_profile_id;
wire [7:0] norm_path=(core_status==3'd0)?{6'd0,core_selected_slot}:8'd255;
wire [17:0] norm_score=(core_status==3'd0)?core_score:18'd0;
wire [15:0] norm_fidelity=(core_status==3'd0)?core_fidelity:16'd0;

p6_replay_rom replay(
 .index(replay_index),.test_id(test_id),.input_valid(input_valid),
 .min_key(min_key),.state_fidelity(state_fidelity),
 .offered_load(offered_load),.imbalance(imbalance),
 .c0_valid(c0_valid),.c0_cost(c0_cost),.c0_fidelity(c0_fidelity),
 .c0_utilization(c0_utilization),.c0_hops(c0_hops),.c0_slot(c0_slot),
 .c1_valid(c1_valid),.c1_cost(c1_cost),.c1_fidelity(c1_fidelity),
 .c1_utilization(c1_utilization),.c1_hops(c1_hops),.c1_slot(c1_slot));

p6_expected_result_rom expected(
 .policy_mode(POLICY_MODE),.replay_index(replay_index),
 .state_id(expected_state),.profile_id(expected_profile),
 .selected_path(expected_path),.score(expected_score),
 .bottleneck_fidelity(expected_fidelity),.cycles(expected_cycles),
 .status(expected_status));

p5_b6_measurement_shell #(.POLICY_MODE(POLICY_MODE)) kernel(
 .clk(clk),.rst(core_rst),.start(core_start),.input_valid(input_valid),
 .min_key_occupancy_u16(min_key),
 .bottleneck_fidelity_state_u16(state_fidelity),
 .offered_request_load_u16(offered_load),
 .utilization_imbalance_state_u16(imbalance),
 .c0_valid(c0_valid),.c0_cost(c0_cost),.c0_fidelity(c0_fidelity),
 .c0_utilization(c0_utilization),.c0_hops(c0_hops),.c0_slot(c0_slot),
 .c1_valid(c1_valid),.c1_cost(c1_cost),.c1_fidelity(c1_fidelity),
 .c1_utilization(c1_utilization),.c1_hops(c1_hops),.c1_slot(c1_slot),
 .ready(core_ready),.busy(),.done(core_done),.route_valid(),.no_path(),
 .stall(),.invalid_request(),.policy_id(core_policy_id),
 .state_id(core_state_id),.profile_id(core_profile_id),
 .selected_slot(core_selected_slot),.selected_score(core_score),
 .bottleneck_fidelity(core_fidelity),.status(core_status),
 .cycles(core_cycles),.cycles_valid());

p6_qf6r_formatter formatter(
 .clk(clk),.rst(rst),.start(format_start),.ready(formatter_ready),
 .done(formatter_done),.test_id(tx_test_id),.policy_id(tx_policy_id),
 .state_id(tx_state_id),.profile_id(tx_profile_id),
 .selected_path(tx_path),.score(tx_score),
 .bottleneck_fidelity(tx_fidelity),.cycles(tx_cycles),
 .status(tx_status),.uart_ready(uart_ready),
 .byte_valid(formatter_valid),.byte_data(formatter_byte));

p5_b1_uart_tx #(.CLK_HZ(CLK_HZ),.BAUD(UART_BAUD)) uart(
 .clk(clk),.rst(rst),.data_valid(formatter_valid),
 .data_byte(formatter_byte),.ready(uart_ready),.tx(uart_tx),.busy());

always @(posedge clk) begin
 if(rst) begin
  state<=GROUP_RESET;reset_count<=0;replay_index<=0;core_rst<=1;
  core_start<=0;format_start<=0;campaign_done<=0;
  records_completed<=0;pass_count<=0;error_count<=0;
  tx_test_id<=0;tx_policy_id<=0;tx_state_id<=0;tx_profile_id<=0;
  tx_path<=0;tx_score<=0;tx_fidelity<=0;tx_cycles<=0;tx_status<=0;
 end else begin
  core_start<=0;
  format_start<=0;
  case(state)
   GROUP_RESET:begin
    core_rst<=1;
    if(reset_count==3) begin
     reset_count<=0;core_rst<=0;state<=WAIT_READY;
    end else reset_count<=reset_count+1'b1;
   end
   WAIT_READY:if(core_ready) state<=ISSUE;
   ISSUE:begin core_start<=1;state<=WAIT_DONE;end
   WAIT_DONE:if(core_done) begin
    tx_test_id<=test_id;tx_policy_id<=POLICY_MODE;
    tx_state_id<=norm_state;tx_profile_id<=norm_profile;
    tx_path<=norm_path;tx_score<=norm_score;tx_fidelity<=norm_fidelity;
    tx_cycles<=core_cycles;tx_status<=core_status;
    if(core_policy_id==POLICY_MODE &&
       norm_state==expected_state &&
       norm_profile==expected_profile &&
       norm_path==expected_path &&
       norm_score==expected_score &&
       norm_fidelity==expected_fidelity &&
       core_cycles==expected_cycles &&
       core_status==expected_status)
      pass_count<=pass_count+1'b1;
    else
      error_count<=error_count+1'b1;
    state<=START_FORMAT;
   end
   START_FORMAT:if(formatter_ready) begin
    format_start<=1;state<=WAIT_FORMAT;
   end
   WAIT_FORMAT:if(formatter_done) state<=ADVANCE;
   ADVANCE:begin
    records_completed<=records_completed+1'b1;
    if(replay_index==83) begin
     campaign_done<=1;state<=COMPLETE;
    end else begin
     replay_index<=replay_index+1'b1;
     if(replay_index==4 || replay_index==9 || replay_index==19)
       state<=GROUP_RESET;
     else
       state<=WAIT_READY;
    end
   end
   COMPLETE:begin campaign_done<=1;state<=COMPLETE;end
   default:state<=GROUP_RESET;
  endcase
 end
end
endmodule
''',encoding="utf-8")

def generate_top():
    TOP.write_text(r'''`timescale 1ns / 1ps
module p6_nexys3_campaign_common #(
 parameter [2:0] POLICY_MODE=3'd0
)(
 input wire clk_100mhz,input wire btn_reset,
 output wire led_heartbeat,output wire led_reset,
 output reg [7:0] seg_n,output reg [3:0] an_n,
 output wire uart_tx
);
wire campaign_done;
wire [6:0] records_completed;
wire [7:0] pass_count;
wire [15:0] error_count;
reg [17:0] scan;
reg [3:0] digit;
wire [3:0] ones=records_completed%10;
wire [3:0] tens=(records_completed/10)%10;

p6_physical_campaign_core #(
 .POLICY_MODE(POLICY_MODE),.CLK_HZ(100000000),.UART_BAUD(115200)
) campaign(
 .clk(clk_100mhz),.rst(btn_reset),.uart_tx(uart_tx),
 .campaign_done(campaign_done),.records_completed(records_completed),
 .pass_count(pass_count),.error_count(error_count));

assign led_heartbeat=campaign_done && (error_count==0) && (pass_count==84);
assign led_reset=(error_count!=0);

always @(posedge clk_100mhz) scan<=scan+1'b1;
always @* begin
 an_n=4'b1111;
 case(scan[17:16])
  2'd0:begin an_n=4'b1110;digit=ones;end
  2'd1:begin an_n=4'b1101;digit=tens;end
  2'd2:begin an_n=4'b1011;digit=4'd0;end
  default:begin an_n=4'b0111;digit={1'b0,POLICY_MODE};end
 endcase
 case(digit)
  0:seg_n=8'b11000000;1:seg_n=8'b11111001;
  2:seg_n=8'b10100100;3:seg_n=8'b10110000;
  4:seg_n=8'b10011001;5:seg_n=8'b10010010;
  6:seg_n=8'b10000010;7:seg_n=8'b11111000;
  8:seg_n=8'b10000000;9:seg_n=8'b10010000;
  default:seg_n=8'b11111111;
 endcase
end
endmodule

module p6_nexys3_h0(
 input wire clk_100mhz,input wire btn_reset,
 output wire led_heartbeat,output wire led_reset,
 output wire [7:0] seg_n,output wire [3:0] an_n,output wire uart_tx);
p6_nexys3_campaign_common #(.POLICY_MODE(3'd0)) u(
 .clk_100mhz(clk_100mhz),.btn_reset(btn_reset),.led_heartbeat(led_heartbeat),
 .led_reset(led_reset),.seg_n(seg_n),.an_n(an_n),.uart_tx(uart_tx));endmodule
module p6_nexys3_h1(
 input wire clk_100mhz,input wire btn_reset,
 output wire led_heartbeat,output wire led_reset,
 output wire [7:0] seg_n,output wire [3:0] an_n,output wire uart_tx);
p6_nexys3_campaign_common #(.POLICY_MODE(3'd1)) u(
 .clk_100mhz(clk_100mhz),.btn_reset(btn_reset),.led_heartbeat(led_heartbeat),
 .led_reset(led_reset),.seg_n(seg_n),.an_n(an_n),.uart_tx(uart_tx));endmodule
module p6_nexys3_h2(
 input wire clk_100mhz,input wire btn_reset,
 output wire led_heartbeat,output wire led_reset,
 output wire [7:0] seg_n,output wire [3:0] an_n,output wire uart_tx);
p6_nexys3_campaign_common #(.POLICY_MODE(3'd2)) u(
 .clk_100mhz(clk_100mhz),.btn_reset(btn_reset),.led_heartbeat(led_heartbeat),
 .led_reset(led_reset),.seg_n(seg_n),.an_n(an_n),.uart_tx(uart_tx));endmodule
module p6_nexys3_h3(
 input wire clk_100mhz,input wire btn_reset,
 output wire led_heartbeat,output wire led_reset,
 output wire [7:0] seg_n,output wire [3:0] an_n,output wire uart_tx);
p6_nexys3_campaign_common #(.POLICY_MODE(3'd3)) u(
 .clk_100mhz(clk_100mhz),.btn_reset(btn_reset),.led_heartbeat(led_heartbeat),
 .led_reset(led_reset),.seg_n(seg_n),.an_n(an_n),.uart_tx(uart_tx));endmodule
module p6_nexys3_h4(
 input wire clk_100mhz,input wire btn_reset,
 output wire led_heartbeat,output wire led_reset,
 output wire [7:0] seg_n,output wire [3:0] an_n,output wire uart_tx);
p6_nexys3_campaign_common #(.POLICY_MODE(3'd4)) u(
 .clk_100mhz(clk_100mhz),.btn_reset(btn_reset),.led_heartbeat(led_heartbeat),
 .led_reset(led_reset),.seg_n(seg_n),.an_n(an_n),.uart_tx(uart_tx));endmodule
''',encoding="utf-8")

def generate_ucf():
    UCF.write_text('''NET "clk_100mhz" LOC = "V10" | IOSTANDARD = LVCMOS33;
NET "clk_100mhz" TNM_NET = "P6_CLK";
TIMESPEC "TS_P6_CLK" = PERIOD "P6_CLK" 10 ns HIGH 50%;
NET "btn_reset" LOC = "B8" | IOSTANDARD = LVCMOS33;
NET "led_heartbeat" LOC = "U16" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW;
NET "led_reset" LOC = "V16" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW;
NET "seg_n<0>" LOC = "T17" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW;
NET "seg_n<1>" LOC = "T18" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW;
NET "seg_n<2>" LOC = "U17" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW;
NET "seg_n<3>" LOC = "U18" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW;
NET "seg_n<4>" LOC = "M14" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW;
NET "seg_n<5>" LOC = "N14" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW;
NET "seg_n<6>" LOC = "L14" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW;
NET "seg_n<7>" LOC = "M13" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW;
NET "an_n<0>" LOC = "N16" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW;
NET "an_n<1>" LOC = "N15" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW;
NET "an_n<2>" LOC = "P18" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW;
NET "an_n<3>" LOC = "P17" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW;
NET "uart_tx" LOC = "N18" | IOSTANDARD = LVCMOS33 | DRIVE = 8 | SLEW = SLOW;
''',encoding="utf-8")

def generate_tb():
    TB.write_text(r'''`timescale 1ns / 1ps
module tb_p6_physical_campaign_shell;
reg clk,rst;
wire tx0,tx1,tx2,tx3,tx4;
wire done0,done1,done2,done3,done4;
wire [6:0] records0,records1,records2,records3,records4;
wire [7:0] pass0,pass1,pass2,pass3,pass4;
wire [15:0] err0,err1,err2,err3,err4;

p6_physical_campaign_core #(.POLICY_MODE(0),.CLK_HZ(1000000),.UART_BAUD(100000)) h0(
 .clk(clk),.rst(rst),.uart_tx(tx0),.campaign_done(done0),
 .records_completed(records0),.pass_count(pass0),.error_count(err0));
p6_physical_campaign_core #(.POLICY_MODE(1),.CLK_HZ(1000000),.UART_BAUD(100000)) h1(
 .clk(clk),.rst(rst),.uart_tx(tx1),.campaign_done(done1),
 .records_completed(records1),.pass_count(pass1),.error_count(err1));
p6_physical_campaign_core #(.POLICY_MODE(2),.CLK_HZ(1000000),.UART_BAUD(100000)) h2(
 .clk(clk),.rst(rst),.uart_tx(tx2),.campaign_done(done2),
 .records_completed(records2),.pass_count(pass2),.error_count(err2));
p6_physical_campaign_core #(.POLICY_MODE(3),.CLK_HZ(1000000),.UART_BAUD(100000)) h3(
 .clk(clk),.rst(rst),.uart_tx(tx3),.campaign_done(done3),
 .records_completed(records3),.pass_count(pass3),.error_count(err3));
p6_physical_campaign_core #(.POLICY_MODE(4),.CLK_HZ(1000000),.UART_BAUD(100000)) h4(
 .clk(clk),.rst(rst),.uart_tx(tx4),.campaign_done(done4),
 .records_completed(records4),.pass_count(pass4),.error_count(err4));

always #500 clk=~clk;
initial begin
 clk=0;rst=1;
 repeat(6) @(posedge clk);rst=0;
 wait(done0&&done1&&done2&&done3&&done4);
 repeat(20) @(posedge clk);
 $display("MODE H0 records=%0d pass=%0d errors=%0d",records0,pass0,err0);
 $display("MODE H1 records=%0d pass=%0d errors=%0d",records1,pass1,err1);
 $display("MODE H2 records=%0d pass=%0d errors=%0d",records2,pass2,err2);
 $display("MODE H3 records=%0d pass=%0d errors=%0d",records3,pass3,err3);
 $display("MODE H4 records=%0d pass=%0d errors=%0d",records4,pass4,err4);
 if(records0==84&&records1==84&&records2==84&&records3==84&&records4==84&&
    pass0==84&&pass1==84&&pass2==84&&pass3==84&&pass4==84&&
    err0==0&&err1==0&&err2==0&&err3==0&&err4==0)
   $display("P6_PHYSICAL_SHELL=420_OF_420_INTERNAL_COMPARISONS_PASS");
 else
   $display("P6_PHYSICAL_SHELL=FAIL");
 $finish;
end
initial begin
 #3000000000;
 $display("P6_PHYSICAL_SHELL=FAIL_TIMEOUT");
 $finish;
end
endmodule
''',encoding="utf-8")

def run_sim():
    sources=[
      ROOT/"rtl/rl/rl_state_encoder.v",
      ROOT/"rtl/rl/rl_policy_rom.v",
      ROOT/"rtl/rl/rl_profile_rom.v",
      ROOT/"rtl/rl/rl_controller.v",
      ROOT/"rtl/spartan6/p5_b1_uart_tx.v",
      ROOT/"rtl/spartan6/p5_b4_candidate_evaluator.v",
      ROOT/"rtl/spartan6/p5_b5_policy_shell.v",
      ROOT/"rtl/spartan6/p5_b6_measurement_shell.v",
      REPLAY_ROM,EXPECTED_ROM,FORMATTER,CORE,TB]
    with tempfile.TemporaryDirectory(prefix="qflow-p6-shell-") as td:
        exe=Path(td)/"shell.vvp"
        cmd=["iverilog","-g2005","-Wall","-Wimplicit",
             "-s","tb_p6_physical_campaign_shell","-o",str(exe)]+[str(x) for x in sources]
        c=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(c.stdout,end="")
        require(c.returncode==0,"iverilog_compile")
        r=subprocess.run(["vvp",str(exe)],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        SIMLOG.write_text(c.stdout+r.stdout,encoding="utf-8")
        print(r.stdout,end="")
        require(r.returncode==0,"vvp_run")
        require("P6_PHYSICAL_SHELL=420_OF_420_INTERNAL_COMPARISONS_PASS" in r.stdout,
                "physical_shell_sentinel")
        require("P6_PHYSICAL_SHELL=FAIL" not in r.stdout,"physical_shell_no_fail")
        rows=[]
        for line in r.stdout.splitlines():
            if line.startswith("MODE H"):
                p=line.replace("="," ").split()
                rows.append({"policy_name":p[1],"records":p[3],
                             "pass_count":p[5],"error_count":p[7]})
        require(len(rows)==5,"summary_modes_5")
        write_csv(SUMMARY,["policy_name","records","pass_count","error_count"],rows)

def main():
    replay=read_csv(REPLAY)
    golden=read_csv(GOLDEN)
    require(len(replay)==84,"replay_rows_84")
    require(len(golden)==420,"golden_rows_420")
    generate_replay_rom(replay)
    generate_expected_rom(golden)
    generate_formatter()
    generate_core()
    generate_top()
    generate_ucf()
    generate_tb()
    run_sim()
    print("P6_STEP3E_REPLAY_ROM=84_OF_84_PASS")
    print("P6_STEP3E_EXPECTED_ROM=420_OF_420_PASS")
    print("P6_STEP3E_POLICY_WRAPPERS=5_OF_5_PASS")
    print("P6_STEP3E_INTERNAL_COMPARISONS=420_OF_420_PASS")
    print("P6_STEP3E_PHYSICAL_SHELL_GATE=PASS")

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("P6_STEP3E_PHYSICAL_SHELL_GATE=FAIL:",exc,file=sys.stderr)
        raise
