`timescale 1ns / 1ps

module tb_p5_b6_measurement_shell;

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

wire ready0,ready1,ready2,ready3,ready4;
wire busy0,busy1,busy2,busy3,busy4;
wire done0,done1,done2,done3,done4;
wire rv0,rv1,rv2,rv3,rv4;
wire np0,np1,np2,np3,np4;
wire stall0,stall1,stall2,stall3,stall4;
wire inv0,inv1,inv2,inv3,inv4;
wire [2:0] pid0,pid1,pid2,pid3,pid4;
wire [7:0] sid0,sid1,sid2,sid3,sid4;
wire [1:0] prof0,prof1,prof2,prof3,prof4;
wire [1:0] sel0,sel1,sel2,sel3,sel4;
wire [17:0] score0,score1,score2,score3,score4;
wire [15:0] bf0,bf1,bf2,bf3,bf4;
wire [2:0] status0,status1,status2,status3,status4;
wire [15:0] cyc0,cyc1,cyc2,cyc3,cyc4;
wire cv0,cv1,cv2,cv3,cv4;

integer sim_cycle;
integer errors;
integer completions;

p5_b6_measurement_shell #(.POLICY_MODE(3'd0)) m0 (
 .clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
 .min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
 .offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
 .c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
 .c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
 .ready(ready0),.busy(busy0),.done(done0),.route_valid(rv0),.no_path(np0),.stall(stall0),.invalid_request(inv0),
 .policy_id(pid0),.state_id(sid0),.profile_id(prof0),.selected_slot(sel0),.selected_score(score0),
 .bottleneck_fidelity(bf0),.status(status0),.cycles(cyc0),.cycles_valid(cv0));

p5_b6_measurement_shell #(.POLICY_MODE(3'd1)) m1 (
 .clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
 .min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
 .offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
 .c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
 .c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
 .ready(ready1),.busy(busy1),.done(done1),.route_valid(rv1),.no_path(np1),.stall(stall1),.invalid_request(inv1),
 .policy_id(pid1),.state_id(sid1),.profile_id(prof1),.selected_slot(sel1),.selected_score(score1),
 .bottleneck_fidelity(bf1),.status(status1),.cycles(cyc1),.cycles_valid(cv1));

p5_b6_measurement_shell #(.POLICY_MODE(3'd2)) m2 (
 .clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
 .min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
 .offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
 .c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
 .c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
 .ready(ready2),.busy(busy2),.done(done2),.route_valid(rv2),.no_path(np2),.stall(stall2),.invalid_request(inv2),
 .policy_id(pid2),.state_id(sid2),.profile_id(prof2),.selected_slot(sel2),.selected_score(score2),
 .bottleneck_fidelity(bf2),.status(status2),.cycles(cyc2),.cycles_valid(cv2));

p5_b6_measurement_shell #(.POLICY_MODE(3'd3)) m3 (
 .clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
 .min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
 .offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
 .c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
 .c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
 .ready(ready3),.busy(busy3),.done(done3),.route_valid(rv3),.no_path(np3),.stall(stall3),.invalid_request(inv3),
 .policy_id(pid3),.state_id(sid3),.profile_id(prof3),.selected_slot(sel3),.selected_score(score3),
 .bottleneck_fidelity(bf3),.status(status3),.cycles(cyc3),.cycles_valid(cv3));

p5_b6_measurement_shell #(.POLICY_MODE(3'd4)) m4 (
 .clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
 .min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
 .offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
 .c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
 .c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
 .ready(ready4),.busy(busy4),.done(done4),.route_valid(rv4),.no_path(np4),.stall(stall4),.invalid_request(inv4),
 .policy_id(pid4),.state_id(sid4),.profile_id(prof4),.selected_slot(sel4),.selected_score(score4),
 .bottleneck_fidelity(bf4),.status(status4),.cycles(cyc4),.cycles_valid(cv4));

always #5 clk = ~clk;
always @(posedge clk) sim_cycle = sim_cycle + 1;

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

task set_scenario;
 input [1:0] scenario;
 begin
  v0=0;v1=0;
  cost0=32'd100;cost1=32'd200;
  fid0=16'd62000;fid1=16'd62000;
  util0=32'd10;util1=32'd10;
  hops0=3'd3;hops1=3'd2;
  slot0=2'd0;slot1=2'd1;
  case(scenario)
   2'd1: begin v0=1;v1=0;end
   2'd2: begin v0=0;v1=1;end
   2'd3: begin v0=1;v1=1;end
  endcase
 end
endtask

task reset_all;
 begin
  rst=1;start=0;input_valid=1;
  repeat(4) @(posedge clk);
  rst=0;
  repeat(2) @(posedge clk);
 end
endtask

task run_case;
 input integer case_id;
 input [7:0] target_state;
 input [1:0] scenario;
 input invalid_case;
 input no_path_case;
 input [1:0] expected_h0_slot;
 input [1:0] expected_other_slot;
 input [2:0] expected_h3_profile;
 input [2:0] expected_h4_profile;
 integer accept_cycle;
 integer guard;
 reg s0,s1,s2,s3,s4;
 integer d0,d1,d2,d3,d4;
 reg crv0,crv1,crv2,crv3,crv4;
 reg cnp0,cnp1,cnp2,cnp3,cnp4;
 reg cinv0,cinv1,cinv2,cinv3,cinv4;
 reg [2:0] cpid0,cpid1,cpid2,cpid3,cpid4;
 reg [7:0] csid0,csid1,csid2,csid3,csid4;
 reg [1:0] cprof0,cprof1,cprof2,cprof3,cprof4;
 reg [1:0] csel0,csel1,csel2,csel3,csel4;
 reg [2:0] cstatus0,cstatus1,cstatus2,cstatus3,cstatus4;
 begin
  set_state(target_state);
  set_scenario(scenario);
  input_valid=!invalid_case;

  while(!(ready0&&ready1&&ready2&&ready3&&ready4)) @(posedge clk);

  @(negedge clk); start=1;
  @(posedge clk); #1; accept_cycle=sim_cycle;
  @(negedge clk); start=0;

  s0=0;s1=0;s2=0;s3=0;s4=0;guard=0;
  crv0=0;crv1=0;crv2=0;crv3=0;crv4=0;
  cnp0=0;cnp1=0;cnp2=0;cnp3=0;cnp4=0;
  cinv0=0;cinv1=0;cinv2=0;cinv3=0;cinv4=0;
  cpid0=0;cpid1=0;cpid2=0;cpid3=0;cpid4=0;
  csid0=0;csid1=0;csid2=0;csid3=0;csid4=0;
  cprof0=0;cprof1=0;cprof2=0;cprof3=0;cprof4=0;
  csel0=0;csel1=0;csel2=0;csel3=0;csel4=0;
  cstatus0=0;cstatus1=0;cstatus2=0;cstatus3=0;cstatus4=0;
  while(!(s0&&s1&&s2&&s3&&s4) && guard<3000) begin
   @(posedge clk); #1; guard=guard+1;

   if(cv0!==done0||cv1!==done1||cv2!==done2||cv3!==done3||cv4!==done4) begin
    $display("FAIL cycles_valid_not_coincident case=%0d",case_id);errors=errors+1;
   end

   if(done0&&!s0) begin
    s0=1;d0=sim_cycle-accept_cycle;completions=completions+1;
    crv0=rv0;cnp0=np0;cinv0=inv0;cpid0=pid0;csid0=sid0;cprof0=prof0;csel0=sel0;cstatus0=status0;
    if(cyc0!=d0) begin $display("FAIL cycle mode=0 case=%0d output=%0d observed=%0d",case_id,cyc0,d0);errors=errors+1;end
   end
   if(done1&&!s1) begin
    s1=1;d1=sim_cycle-accept_cycle;completions=completions+1;
    crv1=rv1;cnp1=np1;cinv1=inv1;cpid1=pid1;csid1=sid1;cprof1=prof1;csel1=sel1;cstatus1=status1;
    if(cyc1!=d1) begin $display("FAIL cycle mode=1 case=%0d output=%0d observed=%0d",case_id,cyc1,d1);errors=errors+1;end
   end
   if(done2&&!s2) begin
    s2=1;d2=sim_cycle-accept_cycle;completions=completions+1;
    crv2=rv2;cnp2=np2;cinv2=inv2;cpid2=pid2;csid2=sid2;cprof2=prof2;csel2=sel2;cstatus2=status2;
    if(cyc2!=d2) begin $display("FAIL cycle mode=2 case=%0d output=%0d observed=%0d",case_id,cyc2,d2);errors=errors+1;end
   end
   if(done3&&!s3) begin
    s3=1;d3=sim_cycle-accept_cycle;completions=completions+1;
    crv3=rv3;cnp3=np3;cinv3=inv3;cpid3=pid3;csid3=sid3;cprof3=prof3;csel3=sel3;cstatus3=status3;
    if(cyc3!=d3) begin $display("FAIL cycle mode=3 case=%0d output=%0d observed=%0d",case_id,cyc3,d3);errors=errors+1;end
   end
   if(done4&&!s4) begin
    s4=1;d4=sim_cycle-accept_cycle;completions=completions+1;
    crv4=rv4;cnp4=np4;cinv4=inv4;cpid4=pid4;csid4=sid4;cprof4=prof4;csel4=sel4;cstatus4=status4;
    if(cyc4!=d4) begin $display("FAIL cycle mode=4 case=%0d output=%0d observed=%0d",case_id,cyc4,d4);errors=errors+1;end
   end
  end

  if(!(s0&&s1&&s2&&s3&&s4)) begin
   $display("FAIL timeout case=%0d",case_id);errors=errors+1;
  end else begin
   $display("MEASURE case=%0d mode=H0 cycles=%0d",case_id,d0);
   $display("MEASURE case=%0d mode=H1 cycles=%0d",case_id,d1);
   $display("MEASURE case=%0d mode=H2 cycles=%0d",case_id,d2);
   $display("MEASURE case=%0d mode=H3 cycles=%0d",case_id,d3);
   $display("MEASURE case=%0d mode=H4 cycles=%0d",case_id,d4);

   if(cpid0!=0||cpid1!=1||cpid2!=2||cpid3!=3||cpid4!=4) begin
    $display("FAIL policy_id case=%0d",case_id);errors=errors+1;
   end

   if(invalid_case) begin
    if(!cinv0||!cinv1||!cinv2||!cinv3||!cinv4||
       crv0||crv1||crv2||crv3||crv4||
       cstatus0!=2||cstatus1!=2||cstatus2!=2||cstatus3!=2||cstatus4!=2) begin
     $display("FAIL invalid result case=%0d",case_id);errors=errors+1;
    end
    if(d0!=1||d1!=1||d2!=1||d3!=1||d4!=1) begin
     $display("FAIL invalid latency case=%0d values=%0d,%0d,%0d,%0d,%0d",case_id,d0,d1,d2,d3,d4);errors=errors+1;
    end
   end else begin
    if(csid0!=target_state||csid1!=target_state||csid2!=target_state||csid3!=target_state||csid4!=target_state) begin
     $display("FAIL state_id case=%0d",case_id);errors=errors+1;
    end

    if(expected_h3_profile<4 && cprof3!=expected_h3_profile[1:0]) begin
     $display("FAIL H3 profile case=%0d actual=%0d expected=%0d",case_id,cprof3,expected_h3_profile);errors=errors+1;
    end
    if(expected_h4_profile<4 && cprof4!=expected_h4_profile[1:0]) begin
     $display("FAIL H4 profile case=%0d actual=%0d expected=%0d",case_id,cprof4,expected_h4_profile);errors=errors+1;
    end

    if(no_path_case) begin
     if(crv0||crv1||crv2||crv3||crv4||!cnp0||!cnp1||!cnp2||!cnp3||!cnp4||
        cstatus0!=1||cstatus1!=1||cstatus2!=1||cstatus3!=1||cstatus4!=1) begin
      $display("FAIL no_path case=%0d",case_id);errors=errors+1;
     end
    end else begin
     if(!crv0||!crv1||!crv2||!crv3||!crv4||cnp0||cnp1||cnp2||cnp3||cnp4||
        cstatus0!=0||cstatus1!=0||cstatus2!=0||cstatus3!=0||cstatus4!=0) begin
      $display("FAIL route result case=%0d",case_id);errors=errors+1;
     end
     if(csel0!=expected_h0_slot) begin
      $display("FAIL H0 slot case=%0d actual=%0d expected=%0d",case_id,csel0,expected_h0_slot);errors=errors+1;
     end
     if(csel1!=expected_other_slot||csel2!=expected_other_slot||
        csel3!=expected_other_slot||csel4!=expected_other_slot) begin
      $display("FAIL H1-H4 slots case=%0d",case_id);errors=errors+1;
     end
    end
   end
  end

  @(posedge clk); #1;
  if(cv0||cv1||cv2||cv3||cv4||done0||done1||done2||done3||done4) begin
   $display("FAIL completion pulse width case=%0d",case_id);errors=errors+1;
  end

  input_valid=1;
 end
endtask

initial begin
 clk=0;rst=1;start=0;input_valid=1;
 min_key=0;state_fid=0;load=0;imbalance=0;
 v0=0;v1=0;cost0=0;cost1=0;fid0=0;fid1=0;util0=0;util1=0;hops0=0;hops1=0;slot0=0;slot1=1;
 sim_cycle=0;errors=0;completions=0;

 reset_all;
 run_case(0,8'd0,2'd1,0,0,0,0,4,4);
 run_case(1,8'd0,2'd2,0,0,1,1,4,4);
 run_case(2,8'd0,2'd3,0,0,1,0,4,4);
 run_case(3,8'd0,2'd0,0,1,0,0,4,4);
 run_case(4,8'd0,2'd0,1,0,0,0,4,4);

 reset_all;
 run_case(5,8'd0,2'd1,0,0,0,0,1,4);
 run_case(6,8'd80,2'd1,0,0,0,0,2,4);
 run_case(7,8'd98,2'd1,0,0,0,0,1,4);
 run_case(8,8'd173,2'd1,0,0,0,0,3,4);
 run_case(9,8'd164,2'd1,0,0,0,0,0,4);

 reset_all;
 run_case(10,8'd0,2'd1,0,0,0,0,4,0);
 run_case(11,8'd25,2'd1,0,0,0,0,4,0);
 run_case(12,8'd25,2'd1,0,0,0,0,4,0);
 run_case(13,8'd25,2'd1,0,0,0,0,4,1);
 run_case(14,8'd17,2'd1,0,0,0,0,4,1);
 run_case(15,8'd17,2'd1,0,0,0,0,4,1);
 run_case(16,8'd17,2'd1,0,0,0,0,4,2);
 run_case(17,8'd104,2'd1,0,0,0,0,4,2);
 run_case(18,8'd104,2'd1,0,0,0,0,4,2);
 run_case(19,8'd104,2'd1,0,0,0,0,4,3);

 if(errors==0 && completions==100)
  $display("P5_B6_MEASUREMENT=100_OF_100_COMPLETIONS_PASS");
 else
  $display("P5_B6_MEASUREMENT=FAIL completions=%0d errors=%0d",completions,errors);

 #20;
 $finish;
end

initial begin
 #10000000;
 $display("P5_B6_MEASUREMENT=FAIL_TIMEOUT");
 $finish;
end

endmodule
