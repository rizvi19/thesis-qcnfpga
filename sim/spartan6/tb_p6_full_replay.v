`timescale 1ns / 1ps
module tb_p6_full_replay;
reg clk,rst,start,input_valid;
reg [15:0] min_key,state_fid,load,imbalance;
reg v0,v1;
reg [31:0] cost0,cost1,util0,util1;
reg [15:0] fid0,fid1;
reg [2:0] hops0,hops1;
reg [1:0] slot0,slot1;
wire ready0,ready1,ready2,ready3,ready4;
wire done0,done1,done2,done3,done4;
wire [2:0] pid0,pid1,pid2,pid3,pid4;
wire [7:0] sid0,sid1,sid2,sid3,sid4;
wire [1:0] prof0,prof1,prof2,prof3,prof4;
wire [1:0] sel0,sel1,sel2,sel3,sel4;
wire [17:0] score0,score1,score2,score3,score4;
wire [15:0] bf0,bf1,bf2,bf3,bf4;
wire [2:0] status0,status1,status2,status3,status4;
wire [15:0] cyc0,cyc1,cyc2,cyc3,cyc4;
wire cv0,cv1,cv2,cv3,cv4;
integer errors,completions;

p5_b6_measurement_shell #(.POLICY_MODE(3'd0)) m0(
.clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
.min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
.offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
.c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
.c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
.ready(ready0),.busy(),.done(done0),.route_valid(),.no_path(),.stall(),.invalid_request(),
.policy_id(pid0),.state_id(sid0),.profile_id(prof0),.selected_slot(sel0),.selected_score(score0),
.bottleneck_fidelity(bf0),.status(status0),.cycles(cyc0),.cycles_valid(cv0));
p5_b6_measurement_shell #(.POLICY_MODE(3'd1)) m1(
.clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
.min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
.offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
.c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
.c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
.ready(ready1),.busy(),.done(done1),.route_valid(),.no_path(),.stall(),.invalid_request(),
.policy_id(pid1),.state_id(sid1),.profile_id(prof1),.selected_slot(sel1),.selected_score(score1),
.bottleneck_fidelity(bf1),.status(status1),.cycles(cyc1),.cycles_valid(cv1));
p5_b6_measurement_shell #(.POLICY_MODE(3'd2)) m2(
.clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
.min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
.offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
.c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
.c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
.ready(ready2),.busy(),.done(done2),.route_valid(),.no_path(),.stall(),.invalid_request(),
.policy_id(pid2),.state_id(sid2),.profile_id(prof2),.selected_slot(sel2),.selected_score(score2),
.bottleneck_fidelity(bf2),.status(status2),.cycles(cyc2),.cycles_valid(cv2));
p5_b6_measurement_shell #(.POLICY_MODE(3'd3)) m3(
.clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
.min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
.offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
.c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
.c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
.ready(ready3),.busy(),.done(done3),.route_valid(),.no_path(),.stall(),.invalid_request(),
.policy_id(pid3),.state_id(sid3),.profile_id(prof3),.selected_slot(sel3),.selected_score(score3),
.bottleneck_fidelity(bf3),.status(status3),.cycles(cyc3),.cycles_valid(cv3));
p5_b6_measurement_shell #(.POLICY_MODE(3'd4)) m4(
.clk(clk),.rst(rst),.start(start),.input_valid(input_valid),
.min_key_occupancy_u16(min_key),.bottleneck_fidelity_state_u16(state_fid),
.offered_request_load_u16(load),.utilization_imbalance_state_u16(imbalance),
.c0_valid(v0),.c0_cost(cost0),.c0_fidelity(fid0),.c0_utilization(util0),.c0_hops(hops0),.c0_slot(slot0),
.c1_valid(v1),.c1_cost(cost1),.c1_fidelity(fid1),.c1_utilization(util1),.c1_hops(hops1),.c1_slot(slot1),
.ready(ready4),.busy(),.done(done4),.route_valid(),.no_path(),.stall(),.invalid_request(),
.policy_id(pid4),.state_id(sid4),.profile_id(prof4),.selected_slot(sel4),.selected_score(score4),
.bottleneck_fidelity(bf4),.status(status4),.cycles(cyc4),.cycles_valid(cv4));

always #5 clk=~clk;

task reset_all;
begin
 rst=1;start=0;input_valid=1;
 repeat(4) @(posedge clk);
 rst=0;
 repeat(2) @(posedge clk);
end
endtask

task run_case;
input integer tid;
input iv;
input [15:0] a,b,c,d;
input x0;
input [31:0] e;
input [15:0] f;
input [31:0] g;
input [2:0] h;
input [1:0] i;
input x1;
input [31:0] j;
input [15:0] k;
input [31:0] l;
input [2:0] m;
input [1:0] n;
integer guard;
reg s0,s1,s2,s3,s4;
begin
 input_valid=iv;min_key=a;state_fid=b;load=c;imbalance=d;
 v0=x0;cost0=e;fid0=f;util0=g;hops0=h;slot0=i;
 v1=x1;cost1=j;fid1=k;util1=l;hops1=m;slot1=n;
 while(!(ready0&&ready1&&ready2&&ready3&&ready4)) @(posedge clk);
 @(negedge clk);start=1;
 @(posedge clk);#1;
 @(negedge clk);start=0;
 s0=0;s1=0;s2=0;s3=0;s4=0;guard=0;
 while(!(s0&&s1&&s2&&s3&&s4)&&guard<5000) begin
   @(posedge clk);#1;guard=guard+1;
   if(cv0!==done0||cv1!==done1||cv2!==done2||cv3!==done3||cv4!==done4) errors=errors+1;
   if(done0&&!s0) begin s0=1;completions=completions+1;
     $display("QF6S,1,%0d,0,%0d,%0d,%0d,%0d,%0d,%0d,%0d",tid,
      status0==2?0:sid0,status0==2?0:prof0,status0==0?sel0:255,
      status0==0?score0:0,status0==0?bf0:0,cyc0,status0); end
   if(done1&&!s1) begin s1=1;completions=completions+1;
     $display("QF6S,1,%0d,1,%0d,%0d,%0d,%0d,%0d,%0d,%0d",tid,
      status1==2?0:sid1,status1==2?0:prof1,status1==0?sel1:255,
      status1==0?score1:0,status1==0?bf1:0,cyc1,status1); end
   if(done2&&!s2) begin s2=1;completions=completions+1;
     $display("QF6S,1,%0d,2,%0d,%0d,%0d,%0d,%0d,%0d,%0d",tid,
      status2==2?0:sid2,status2==2?0:prof2,status2==0?sel2:255,
      status2==0?score2:0,status2==0?bf2:0,cyc2,status2); end
   if(done3&&!s3) begin s3=1;completions=completions+1;
     $display("QF6S,1,%0d,3,%0d,%0d,%0d,%0d,%0d,%0d,%0d",tid,
      status3==2?0:sid3,status3==2?0:prof3,status3==0?sel3:255,
      status3==0?score3:0,status3==0?bf3:0,cyc3,status3); end
   if(done4&&!s4) begin s4=1;completions=completions+1;
     $display("QF6S,1,%0d,4,%0d,%0d,%0d,%0d,%0d,%0d,%0d",tid,
      status4==2?0:sid4,status4==2?0:prof4,status4==0?sel4:255,
      status4==0?score4:0,status4==0?bf4:0,cyc4,status4); end
 end
 if(!(s0&&s1&&s2&&s3&&s4)) begin
   $display("P6_RTL_REPLAY=FAIL_TIMEOUT_%0d",tid);$finish;
 end
 @(posedge clk);#1;
 input_valid=1;
end
endtask

initial begin
 clk=0;rst=1;start=0;input_valid=1;
 min_key=0;state_fid=0;load=0;imbalance=0;
 v0=0;v1=0;cost0=0;cost1=0;fid0=0;fid1=0;util0=0;util1=0;
 hops0=0;hops1=0;slot0=0;slot1=1;errors=0;completions=0;
 reset_all;
 run_case(0,1,0,0,0,0,1,100,62000,10,3,0,0,200,62000,10,2,1);
 run_case(1,1,0,0,0,0,0,100,62000,10,3,0,1,200,62000,10,2,1);
 run_case(2,1,0,0,0,0,1,100,62000,10,3,0,1,200,62000,10,2,1);
 run_case(3,1,0,0,0,0,0,100,62000,10,3,0,0,200,62000,10,2,1);
 run_case(4,0,0,0,0,0,0,100,62000,10,3,0,0,200,62000,10,2,1);
 reset_all;
 run_case(5,1,0,0,0,0,1,100,62000,10,3,0,0,200,62000,10,2,1);
 run_case(6,1,16384,58982,0,0,1,100,62000,10,3,0,0,200,62000,10,2,1);
 run_case(7,1,16384,60948,0,16384,1,100,62000,10,3,0,0,200,62000,10,2,1);
 run_case(8,1,32768,60948,49151,8192,1,100,62000,10,3,0,0,200,62000,10,2,1);
 run_case(9,1,32768,60948,16384,0,1,100,62000,10,3,0,0,200,62000,10,2,1);
 reset_all;
 run_case(10,1,0,0,0,0,1,100,62000,10,3,0,0,200,62000,10,2,1);
 run_case(11,1,0,58982,32768,8192,1,100,62000,10,3,0,0,200,62000,10,2,1);
 run_case(12,1,0,58982,32768,8192,1,100,62000,10,3,0,0,200,62000,10,2,1);
 run_case(13,1,0,58982,32768,8192,1,100,62000,10,3,0,0,200,62000,10,2,1);
 run_case(14,1,0,58982,0,8192,1,100,62000,10,3,0,0,200,62000,10,2,1);
 run_case(15,1,0,58982,0,8192,1,100,62000,10,3,0,0,200,62000,10,2,1);
 run_case(16,1,0,58982,0,8192,1,100,62000,10,3,0,0,200,62000,10,2,1);
 run_case(17,1,16384,60948,32768,0,1,100,62000,10,3,0,0,200,62000,10,2,1);
 run_case(18,1,16384,60948,32768,0,1,100,62000,10,3,0,0,200,62000,10,2,1);
 run_case(19,1,16384,60948,32768,0,1,100,62000,10,3,0,0,200,62000,10,2,1);
 reset_all;
 run_case(1000,1,3224,61664,38919,6290,1,39474,61286,55669,3,0,1,43826,62368,70508,3,1);
 run_case(1001,1,15718,62578,27797,3095,1,23794,62212,49707,1,0,1,16378,61234,7054,5,1);
 run_case(1002,1,16993,61471,25509,3757,1,45832,62862,63461,5,0,1,48462,61275,48225,1,1);
 run_case(1003,1,31426,62899,32297,7712,1,35451,61520,4666,4,0,0,28749,62483,36716,2,1);
 run_case(1004,1,5264,63399,25008,18738,1,43039,62449,1390,2,0,1,57691,62469,67932,4,1);
 run_case(1005,1,17337,63605,28863,10806,1,32382,63702,59406,1,0,1,27836,63661,29337,5,1);
 run_case(1006,1,15915,62906,30627,15654,1,6701,63058,48685,2,0,1,18910,62560,66224,4,1);
 run_case(1007,1,33230,62425,30314,17093,0,32287,62235,66688,4,0,0,27485,63368,52690,2,1);
 run_case(1008,1,4499,61921,26918,10879,1,41198,62463,79765,3,0,1,44399,63040,15902,3,1);
 run_case(1009,1,16065,63533,37215,15032,1,42100,61896,34665,4,0,1,39531,64393,26154,2,1);
 run_case(1010,1,18230,60553,31735,15168,1,48691,60475,34814,1,0,1,54325,60347,23193,5,1);
 run_case(1011,1,34005,62502,20113,17564,0,8080,62203,58643,4,0,1,5846,63744,30543,2,1);
 run_case(1012,1,3901,61716,21232,17843,1,4164,62648,41368,4,0,1,18416,62094,50006,2,1);
 run_case(1013,1,17108,61852,30092,12381,1,49528,62457,28695,3,0,1,45804,60407,12324,3,1);
 run_case(1014,1,17183,60893,24253,12421,1,2798,61847,42254,5,0,1,18737,60269,68949,1,1);
 run_case(1015,0,33158,61014,27720,20391,0,43444,62626,28453,4,0,0,40652,61166,4820,2,1);
 run_case(1016,1,40039,58358,21360,10142,1,8493,59981,836,2,0,1,13134,58982,51105,4,1);
 run_case(1017,1,34765,58551,37391,17947,1,25185,58982,60483,4,0,1,19113,59847,79643,2,1);
 run_case(1018,1,35389,60700,38851,16893,1,6615,61098,50965,5,0,1,14538,59232,38892,1,1);
 run_case(1019,1,40953,63420,18523,18922,1,5003,65080,43417,3,0,0,2252,62057,12601,3,1);
 run_case(1020,1,32920,57951,26396,18318,1,48674,59813,24876,5,0,1,63780,59499,44603,1,1);
 run_case(1021,1,35568,59554,22385,7929,1,29797,61252,52016,2,0,1,23839,60118,75491,4,1);
 run_case(1022,1,42608,61008,17746,7178,1,4248,59603,55677,4,0,1,18989,62213,25622,2,1);
 run_case(1023,1,42206,63618,17856,12701,0,47305,63941,43851,3,0,0,42269,62092,42944,3,1);
 run_case(1024,1,43630,56895,20898,8343,1,14004,58982,34739,4,0,1,16468,59372,18287,2,1);
 run_case(1025,1,33449,59055,32249,18178,1,41578,58982,45382,1,0,1,40168,58982,11306,5,1);
 run_case(1026,1,44161,61058,39544,3785,1,11860,62312,49875,1,0,1,16606,62780,43721,5,1);
 run_case(1027,1,35093,63978,36072,12860,0,13021,62676,78127,2,0,1,10431,63446,51867,4,1);
 run_case(1028,1,29025,56736,23481,18857,1,16341,60703,59345,5,0,1,18876,58982,39761,1,1);
 run_case(1029,1,28382,59490,39627,12184,1,35821,59515,17760,2,0,1,34202,58982,38210,4,1);
 run_case(1030,1,41075,61148,30915,22532,1,9210,62328,9266,2,0,1,14983,62545,28768,4,1);
 run_case(1031,1,38335,63102,32392,3848,1,40055,63034,5127,5,0,1,34193,61982,74677,1,1);
 run_case(1032,1,41707,61100,12554,2867,1,25950,60167,22710,1,0,1,40812,62348,13219,5,1);
 run_case(1033,1,35288,61228,18685,9613,1,44860,62473,31797,3,0,1,37584,61948,39913,3,1);
 run_case(1034,1,45846,64259,36712,24153,1,34365,62513,70580,3,0,1,40275,65535,14084,3,1);
 run_case(1035,1,44264,63964,51064,41423,1,16328,65242,56189,5,0,0,14189,62846,26528,1,1);
 run_case(1036,1,35411,61184,12518,2221,1,42511,59445,44787,4,0,1,53897,62141,71494,2,1);
 run_case(1037,1,44154,61615,21724,11611,1,33181,60264,76765,1,0,1,28081,60678,25338,5,1);
 run_case(1038,1,31875,61020,35946,24141,1,15079,62659,28947,2,0,1,20606,61295,4813,4,1);
 run_case(1039,1,32360,62530,50089,41901,0,24130,62991,63772,1,0,0,18386,61605,14143,5,1);
 run_case(1040,1,33361,63564,14011,5481,1,38426,63736,2199,4,0,1,54221,62742,78520,2,1);
 run_case(1041,1,40829,62043,21968,11949,1,11184,62427,35599,5,0,1,7980,63101,45417,1,1);
 run_case(1042,1,36348,63891,34084,20737,1,47809,64352,30865,5,0,1,50106,62923,36080,1,1);
 run_case(1043,1,46931,61221,50278,38213,0,21596,60176,60580,4,0,1,17553,60556,3545,2,1);
 run_case(1044,1,36405,60916,12758,2303,1,29557,60662,76647,1,0,1,44341,62642,57519,5,1);
 run_case(1045,1,42827,63199,19613,10129,1,42224,62895,15981,5,0,1,41620,62691,73213,1,1);
 run_case(1046,1,33250,61128,38101,23932,1,17854,60356,55737,2,0,1,27817,61143,75044,4,1);
 run_case(1047,0,45988,63712,51940,40064,0,32688,64931,10254,5,0,0,30903,62255,73028,1,1);
 run_case(1048,1,7874,59726,42554,34469,1,15333,59537,27660,5,0,1,21292,60865,17636,1,1);
 run_case(1049,1,58323,56918,23524,16048,1,7285,58982,39836,5,0,1,5215,58982,21072,1,1);
 run_case(1050,1,27646,59441,35127,41289,1,32102,58982,62752,4,0,1,37479,58982,73715,2,1);
 run_case(1051,1,12311,60354,13231,6851,1,23869,60768,49053,5,0,0,17173,61698,15096,1,1);
 run_case(1052,1,47535,63233,7262,13962,1,20526,64910,650,5,0,1,25052,65032,45528,1,1);
 run_case(1053,1,17063,64225,19436,25821,1,15623,65535,39529,3,0,1,10555,63593,53783,3,1);
 run_case(1054,1,38809,63136,2100,7801,1,8585,61827,30030,4,0,1,12088,64712,8102,2,1);
 run_case(1055,1,43146,62247,64933,7294,0,10756,61020,23559,2,0,0,8567,60678,54541,4,1);
 run_case(1056,1,20983,57414,59675,5274,1,48668,59367,24100,2,0,1,53161,58982,36425,4,1);
 run_case(1057,1,14160,64690,14160,20896,1,21640,64570,43947,1,0,1,13825,63931,35316,5,1);
 run_case(1058,1,52159,59683,54140,34178,1,49703,61413,14430,5,0,1,61804,58982,45352,1,1);
 run_case(1059,1,8626,56791,14869,24344,0,514,58982,55854,1,0,1,1,58982,78206,5,1);
 run_case(1060,1,17030,56025,25792,38402,1,15551,58982,6250,1,0,1,28650,58982,52526,5,1);
 run_case(1061,1,28894,64084,4631,3592,1,15442,63990,67690,2,0,1,14348,64427,55322,4,1);
 run_case(1062,1,42791,61767,48200,4551,1,5436,62081,5991,3,0,1,8561,62965,10862,3,1);
 run_case(1063,1,60606,62599,54448,15772,1,33288,63277,58682,3,0,1,26328,63930,58278,3,1);

 if(errors==0&&completions==420)
   $display("P6_RTL_REPLAY=420_OF_420_COMPLETIONS_PASS");
 else
   $display("P6_RTL_REPLAY=FAIL completions=%0d errors=%0d",completions,errors);
 #20;$finish;
end
initial begin
 #100000000;$display("P6_RTL_REPLAY=FAIL_GLOBAL_TIMEOUT");$finish;
end
endmodule
