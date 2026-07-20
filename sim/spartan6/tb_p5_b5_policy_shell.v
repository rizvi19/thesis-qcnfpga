`timescale 1ns / 1ps

module tb_p5_b5_policy_shell;

reg clk;
reg rst;
reg start;
reg input_valid;

reg [15:0] min_key;
reg [15:0] state_fid;
reg [15:0] load;
reg [15:0] imbalance;

reg v0, v1;
reg [31:0] cost0, cost1, util0, util1;
reg [15:0] fid0, fid1;
reg [2:0] hops0, hops1;
reg [1:0] slot0, slot1;

wire ready0, ready1, ready2, ready3, ready4;
wire busy0, busy1, busy2, busy3, busy4;
wire done0, done1, done2, done3, done4;
wire rv0, rv1, rv2, rv3, rv4;
wire np0, np1, np2, np3, np4;
wire st0, st1, st2, st3, st4;
wire inv0, inv1, inv2, inv3, inv4;
wire [2:0] pid0, pid1, pid2, pid3, pid4;
wire [7:0] sid0, sid1, sid2, sid3, sid4;
wire [1:0] prof0, prof1, prof2, prof3, prof4;
wire [1:0] sel0, sel1, sel2, sel3, sel4;
wire [17:0] score0, score1, score2, score3, score4;
wire [15:0] bf0, bf1, bf2, bf3, bf4;
wire [2:0] status0, status1, status2, status3, status4;
wire [15:0] cyc0, cyc1, cyc2, cyc3, cyc4;
wire cv0, cv1, cv2, cv3, cv4;

integer errors;
integer checks;

p5_b5_policy_shell #(.POLICY_MODE(3'd0)) m0 (
 .clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
 .min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
 .offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
 .c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
 .c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
 .ready(ready0),.busy(busy0),.done(done0),.route_valid(rv0),.no_path(np0),.stall(st0),.invalid_request(inv0),
 .policy_id(pid0),.state_id(sid0),.profile_id(prof0),.selected_slot(sel0),.selected_score(score0),
 .bottleneck_fidelity(bf0),.status(status0),.cycles(cyc0),.cycles_valid(cv0));

p5_b5_policy_shell #(.POLICY_MODE(3'd1)) m1 (
 .clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
 .min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
 .offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
 .c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
 .c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
 .ready(ready1),.busy(busy1),.done(done1),.route_valid(rv1),.no_path(np1),.stall(st1),.invalid_request(inv1),
 .policy_id(pid1),.state_id(sid1),.profile_id(prof1),.selected_slot(sel1),.selected_score(score1),
 .bottleneck_fidelity(bf1),.status(status1),.cycles(cyc1),.cycles_valid(cv1));

p5_b5_policy_shell #(.POLICY_MODE(3'd2)) m2 (
 .clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
 .min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
 .offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
 .c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
 .c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
 .ready(ready2),.busy(busy2),.done(done2),.route_valid(rv2),.no_path(np2),.stall(st2),.invalid_request(inv2),
 .policy_id(pid2),.state_id(sid2),.profile_id(prof2),.selected_slot(sel2),.selected_score(score2),
 .bottleneck_fidelity(bf2),.status(status2),.cycles(cyc2),.cycles_valid(cv2));

p5_b5_policy_shell #(.POLICY_MODE(3'd3)) m3 (
 .clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
 .min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
 .offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
 .c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
 .c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
 .ready(ready3),.busy(busy3),.done(done3),.route_valid(rv3),.no_path(np3),.stall(st3),.invalid_request(inv3),
 .policy_id(pid3),.state_id(sid3),.profile_id(prof3),.selected_slot(sel3),.selected_score(score3),
 .bottleneck_fidelity(bf3),.status(status3),.cycles(cyc3),.cycles_valid(cv3));

p5_b5_policy_shell #(.POLICY_MODE(3'd4)) m4 (
 .clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
 .min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
 .offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
 .c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
 .c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
 .ready(ready4),.busy(busy4),.done(done4),.route_valid(rv4),.no_path(np4),.stall(st4),.invalid_request(inv4),
 .policy_id(pid4),.state_id(sid4),.profile_id(prof4),.selected_slot(sel4),.selected_score(score4),
 .bottleneck_fidelity(bf4),.status(status4),.cycles(cyc4),.cycles_valid(cv4));

always #5 clk = ~clk;

task set_state;
 input [7:0] target;
 begin
  case(target[7:6])
   2'd0:min_key=16'd0; 2'd1:min_key=16'd16384;
   2'd2:min_key=16'd32768; default:min_key=16'd49151;
  endcase
  case(target[5:4])
   2'd0:state_fid=16'd0; 2'd1:state_fid=16'd58982;
   2'd2:state_fid=16'd60948; default:state_fid=16'd62914;
  endcase
  case(target[3:2])
   2'd0:load=16'd0; 2'd1:load=16'd16384;
   2'd2:load=16'd32768; default:load=16'd49151;
  endcase
  case(target[1:0])
   2'd0:imbalance=16'd0; 2'd1:imbalance=16'd8192;
   2'd2:imbalance=16'd16384; default:imbalance=16'd32768;
  endcase
 end
endtask

task reset_all;
 begin
  rst=1'b1; start=1'b0; input_valid=1'b1;
  repeat(4) @(posedge clk);
  rst=1'b0;
  repeat(2) @(posedge clk);
 end
endtask

task set_scenario;
 input [1:0] scenario;
 begin
  v0=1'b0; v1=1'b0;
  cost0=32'd100; cost1=32'd200;
  fid0=16'd62000; fid1=16'd62000;
  util0=32'd10; util1=32'd10;
  hops0=3'd3; hops1=3'd2;
  slot0=2'd0; slot1=2'd1;
  case(scenario)
   2'd1: begin v0=1'b1; v1=1'b0; end
   2'd2: begin v0=1'b0; v1=1'b1; end
   2'd3: begin v0=1'b1; v1=1'b1; end
   default: begin v0=1'b0; v1=1'b0; end
  endcase
 end
endtask

task run_case;
 input [7:0] target_state;
 input [1:0] scenario;
 input expected_no_path;
 input [1:0] expected_h0_slot;
 input [1:0] expected_other_slot;
 input [2:0] expected_h3_profile;
 input [2:0] expected_h4_profile;
 integer guard;
 reg seen0,seen1,seen2,seen3,seen4;
 reg crv0,crv1,crv2,crv3,crv4;
 reg cnp0,cnp1,cnp2,cnp3,cnp4;
 reg [1:0] csel0,csel1,csel2,csel3,csel4;
 reg [1:0] cprof0,cprof1,cprof2,cprof3,cprof4;
 reg [7:0] csid0,csid1,csid2,csid3,csid4;
 reg [2:0] cpid0,cpid1,cpid2,cpid3,cpid4;
 reg [2:0] cstat0,cstat1,cstat2,cstat3,cstat4;
 begin
  set_state(target_state);
  set_scenario(scenario);
  while(!(ready0&&ready1&&ready2&&ready3&&ready4)) @(posedge clk);
  start=1'b1; input_valid=1'b1;
  @(posedge clk); #1; start=1'b0;

  seen0=0;seen1=0;seen2=0;seen3=0;seen4=0;guard=0;
  while(!(seen0&&seen1&&seen2&&seen3&&seen4) && guard<2000) begin
   @(posedge clk); #1; guard=guard+1;
   if(done0&&!seen0) begin seen0=1;crv0=rv0;cnp0=np0;csel0=sel0;cprof0=prof0;csid0=sid0;cpid0=pid0;cstat0=status0;end
   if(done1&&!seen1) begin seen1=1;crv1=rv1;cnp1=np1;csel1=sel1;cprof1=prof1;csid1=sid1;cpid1=pid1;cstat1=status1;end
   if(done2&&!seen2) begin seen2=1;crv2=rv2;cnp2=np2;csel2=sel2;cprof2=prof2;csid2=sid2;cpid2=pid2;cstat2=status2;end
   if(done3&&!seen3) begin seen3=1;crv3=rv3;cnp3=np3;csel3=sel3;cprof3=prof3;csid3=sid3;cpid3=pid3;cstat3=status3;end
   if(done4&&!seen4) begin seen4=1;crv4=rv4;cnp4=np4;csel4=sel4;cprof4=prof4;csid4=sid4;cpid4=pid4;cstat4=status4;end
  end

  if(!(seen0&&seen1&&seen2&&seen3&&seen4)) begin
   $display("FAIL timeout state=%0d scenario=%0d",target_state,scenario); errors=errors+1;
  end else begin
   checks=checks+5;
   if(cpid0!=0||cpid1!=1||cpid2!=2||cpid3!=3||cpid4!=4) begin
    $display("FAIL policy IDs"); errors=errors+1;
   end
   if(csid0!=target_state||csid1!=target_state||csid2!=target_state||csid3!=target_state||csid4!=target_state) begin
    $display("FAIL state IDs target=%0d got=%0d,%0d,%0d,%0d,%0d",target_state,csid0,csid1,csid2,csid3,csid4); errors=errors+1;
   end
   if(cprof0!=0||cprof1!=0||cprof2!=0) begin
    $display("FAIL fixed profiles"); errors=errors+1;
   end
   if(expected_h3_profile<4 && cprof3!=expected_h3_profile[1:0]) begin
    $display("FAIL H3 profile state=%0d actual=%0d expected=%0d",target_state,cprof3,expected_h3_profile); errors=errors+1;
   end
   if(expected_h4_profile<4 && cprof4!=expected_h4_profile[1:0]) begin
    $display("FAIL H4 profile state=%0d actual=%0d expected=%0d",target_state,cprof4,expected_h4_profile); errors=errors+1;
   end

   if(expected_no_path) begin
    if(crv0||crv1||crv2||crv3||crv4||!cnp0||!cnp1||!cnp2||!cnp3||!cnp4) begin
     $display("FAIL no-path result state=%0d",target_state); errors=errors+1;
    end
    if(cstat0!=1||cstat1!=1||cstat2!=1||cstat3!=1||cstat4!=1) begin
     $display("FAIL no-path status"); errors=errors+1;
    end
   end else begin
    if(!crv0||!crv1||!crv2||!crv3||!crv4||cnp0||cnp1||cnp2||cnp3||cnp4) begin
     $display("FAIL route-valid result state=%0d",target_state); errors=errors+1;
    end
    if(csel0!=expected_h0_slot) begin
     $display("FAIL H0 slot actual=%0d expected=%0d",csel0,expected_h0_slot); errors=errors+1;
    end
    if(csel1!=expected_other_slot||csel2!=expected_other_slot||csel3!=expected_other_slot||csel4!=expected_other_slot) begin
     $display("FAIL H1-H4 slots actual=%0d,%0d,%0d,%0d expected=%0d",csel1,csel2,csel3,csel4,expected_other_slot); errors=errors+1;
    end
    if(cstat0!=0||cstat1!=0||cstat2!=0||cstat3!=0||cstat4!=0) begin
     $display("FAIL OK status"); errors=errors+1;
    end
   end

   if(cv0||cv1||cv2||cv3||cv4||cyc0!=0||cyc1!=0||cyc2!=0||cyc3!=0||cyc4!=0) begin
    $display("FAIL B6 placeholder contract"); errors=errors+1;
   end
  end
  $display("CASE state=%0d scenario=%0d complete",target_state,scenario);
 end
endtask

task invalid_case;
 integer guard;
 reg s0,s1,s2,s3,s4;
 begin
  while(!(ready0&&ready1&&ready2&&ready3&&ready4)) @(posedge clk);
  input_valid=1'b0; start=1'b1;
  @(posedge clk); #1; start=1'b0;
  s0=0;s1=0;s2=0;s3=0;s4=0;guard=0;
  while(!(s0&&s1&&s2&&s3&&s4) && guard<20) begin
   @(posedge clk); #1; guard=guard+1;
   if(done0) begin s0=1;if(!inv0||status0!=2||rv0) errors=errors+1;end
   if(done1) begin s1=1;if(!inv1||status1!=2||rv1) errors=errors+1;end
   if(done2) begin s2=1;if(!inv2||status2!=2||rv2) errors=errors+1;end
   if(done3) begin s3=1;if(!inv3||status3!=2||rv3) errors=errors+1;end
   if(done4) begin s4=1;if(!inv4||status4!=2||rv4) errors=errors+1;end
  end
  checks=checks+5;
  if(!(s0&&s1&&s2&&s3&&s4)) begin $display("FAIL invalid timeout");errors=errors+1;end
  input_valid=1'b1;
 end
endtask

task h4_stall_case;
 integer guard;
 reg saw_stall;
 begin
  set_state(8'd0); set_scenario(2'd1);
  while(!ready4) @(posedge clk);
  start=1'b1; input_valid=1'b1;
  @(posedge clk); #1; start=1'b0;
  @(posedge clk); #1; start=1'b1;
  @(posedge clk); #1;
  saw_stall=st4;
  start=1'b0;
  guard=0;
  while(!done4 && guard<2000) begin @(posedge clk); #1; guard=guard+1;end
  checks=checks+1;
  if(!saw_stall) begin $display("FAIL H4 stall pulse");errors=errors+1;end
  if(guard>=2000) begin $display("FAIL H4 stall transaction timeout");errors=errors+1;end
 end
endtask

initial begin
 clk=0;rst=1;start=0;input_valid=1;
 min_key=0;state_fid=0;load=0;imbalance=0;
 v0=0;v1=0;cost0=0;cost1=0;fid0=0;fid1=0;util0=0;util1=0;hops0=0;hops1=0;slot0=0;slot1=1;
 errors=0;checks=0;

 reset_all;
 run_case(8'd0,2'd0,1'b1,2'd0,2'd0,3'd4,3'd4);
 run_case(8'd0,2'd1,1'b0,2'd0,2'd0,3'd4,3'd4);
 run_case(8'd0,2'd2,1'b0,2'd1,2'd1,3'd4,3'd4);
 run_case(8'd0,2'd3,1'b0,2'd1,2'd0,3'd4,3'd4);

 reset_all;
 run_case(8'd0,  2'd1,1'b0,2'd0,2'd0,3'd1,3'd4);
 run_case(8'd80, 2'd1,1'b0,2'd0,2'd0,3'd2,3'd4);
 run_case(8'd98, 2'd1,1'b0,2'd0,2'd0,3'd1,3'd4);
 run_case(8'd173,2'd1,1'b0,2'd0,2'd0,3'd3,3'd4);
 run_case(8'd164,2'd1,1'b0,2'd0,2'd0,3'd0,3'd4);

 reset_all;
 run_case(8'd0,  2'd1,1'b0,2'd0,2'd0,3'd4,3'd0);
 run_case(8'd25, 2'd1,1'b0,2'd0,2'd0,3'd4,3'd0);
 run_case(8'd25, 2'd1,1'b0,2'd0,2'd0,3'd4,3'd0);
 run_case(8'd25, 2'd1,1'b0,2'd0,2'd0,3'd4,3'd1);
 run_case(8'd17, 2'd1,1'b0,2'd0,2'd0,3'd4,3'd1);
 run_case(8'd17, 2'd1,1'b0,2'd0,2'd0,3'd4,3'd1);
 run_case(8'd17, 2'd1,1'b0,2'd0,2'd0,3'd4,3'd2);
 run_case(8'd104,2'd1,1'b0,2'd0,2'd0,3'd4,3'd2);
 run_case(8'd104,2'd1,1'b0,2'd0,2'd0,3'd4,3'd2);
 run_case(8'd104,2'd1,1'b0,2'd0,2'd0,3'd4,3'd3);

 reset_all;
 invalid_case;

 reset_all;
 h4_stall_case;

 if(errors==0 && checks==101)
  $display("P5_B5_HOST_TEST=101_OF_101_MODE_RESULTS_PASS");
 else
  $display("P5_B5_HOST_TEST=FAIL checks=%0d errors=%0d",checks,errors);

 #20;
 $finish;
end

initial begin
 #5000000;
 $display("P5_B5_HOST_TEST=FAIL_TIMEOUT");
 $finish;
end

endmodule
