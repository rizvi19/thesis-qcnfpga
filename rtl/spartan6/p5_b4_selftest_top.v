`timescale 1ns / 1ps
module p5_b4_selftest_top(
 input wire clk_100mhz, input wire btn_reset,
 output wire led_heartbeat, output wire led_pass, output wire led_fail,
 output wire led_done, output wire [7:0] seg_n, output wire [3:0] an_n);
 reg [25:0] hb; reg [4:0] idx; reg start; reg pass; reg fail; reg finished;
 reg v0,v1; reg [31:0] c0,c1,u0,u1; reg [15:0] f0,f1;
 reg [2:0] h0,h1; reg [1:0] s0,s1,l0,l1,l2; reg [1:0] exp_slot; reg [17:0] exp_score;
 wire ready,done,route_valid,no_path; wire [1:0] selected_slot; wire [17:0] selected_score;
 p5_b4_candidate_evaluator dut(clk_100mhz,btn_reset,start,ready,v0,c0,f0,u0,h0,s0,v1,c1,f1,u1,h1,s1,l0,l1,l2,done,route_valid,no_path,selected_slot,selected_score);
 p5_b1_sevenseg display(clk_100mhz,btn_reset,16'hB410,seg_n,an_n);
 assign led_heartbeat=hb[25]; assign led_pass=pass; assign led_fail=fail; assign led_done=finished;
 always @* begin
   v0=1;v1=1;c0=100;c1=200;f0=62000;f1=61000;u0=500;u1=700;h0=2;h1=3;s0=0;s1=1;l0=2;l1=2;l2=1;exp_slot=0;exp_score=0;
   case(idx)
    0: begin v0=0;v1=0;exp_slot=0;exp_score=0;end
    1: begin v1=0;exp_slot=0;exp_score=0;end
    2: begin v0=0;exp_slot=1;exp_score=0;end
    3: begin c0=100;c1=100;f0=60000;f1=60000;u0=10;u1=10;h0=2;h1=2;exp_slot=0;exp_score=0;end
    4: begin c0=200;c1=100;f0=60000;f1=60000;u0=10;u1=10;exp_slot=1;exp_score=0;end
    5: begin c0=100;c1=200;f0=60000;f1=60000;u0=10;u1=10;exp_slot=0;exp_score=0;end
    6: begin c0=100;c1=100;f0=59000;f1=62000;u0=10;u1=10;exp_slot=1;exp_score=0;end
    7: begin c0=100;c1=100;f0=62000;f1=59000;u0=10;u1=10;exp_slot=0;exp_score=0;end
    8: begin c0=100;c1=100;f0=60000;f1=60000;u0=20;u1=10;exp_slot=1;exp_score=0;end
    9: begin c0=100;c1=100;f0=60000;f1=60000;u0=10;u1=20;exp_slot=0;exp_score=0;end
    10: begin c0=100;c1=100;f0=60000;f1=60000;u0=10;u1=10;h0=3;h1=2;exp_slot=1;exp_score=0;end
    11: begin c0=100;c1=100;f0=60000;f1=60000;u0=10;u1=10;s0=1;s1=0;exp_slot=1;exp_score=0;end
    default: begin v1=0;exp_slot=0;exp_score=0;end
   endcase
 end
 always @(posedge clk_100mhz) begin
   if(btn_reset) begin hb<=0;idx<=0;start<=0;pass<=0;fail<=0;finished<=0;end
   else begin hb<=hb+1'b1; start<=0;
     if(!finished && ready && !start) start<=1;
     if(done) begin
       if(idx==0) begin if(!no_path || route_valid) fail<=1; end
       else if(!route_valid || no_path || selected_slot!=exp_slot) fail<=1;
       if(idx==15) begin finished<=1; pass<=!fail; end else idx<=idx+1'b1;
     end
   end
 end
endmodule
