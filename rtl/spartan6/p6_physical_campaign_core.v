`timescale 1ns / 1ps
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
