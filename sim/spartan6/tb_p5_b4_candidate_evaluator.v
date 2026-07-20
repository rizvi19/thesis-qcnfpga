`timescale 1ns/1ps
module tb_p5_b4_candidate_evaluator;
 reg clk=0,rst=1,start=0; always #5 clk=~clk;
 reg v0,v1; reg[31:0] c0,c1,u0,u1; reg[15:0] f0,f1;reg[2:0]h0,h1;reg[1:0]s0,s1,l0,l1,l2;
 wire ready,done,route_valid,no_path;wire[1:0]slot;wire[17:0]score;
 reg [198:0] vectors[0:518]; integer i,errors,cycles; reg eno;reg[1:0]eslot;reg[17:0]escore;
 p5_b4_candidate_evaluator dut(clk,rst,start,ready,v0,c0,f0,u0,h0,s0,v1,c1,f1,u1,h1,s1,l0,l1,l2,done,route_valid,no_path,slot,score);
 initial begin
  $readmemh("sim/spartan6/p5_b4_vectors.mem",vectors);errors=0;#23;rst=0;
  for(i=0;i<519;i=i+1) begin
   while(!ready) @(posedge clk);
   {v0,c0,f0,u0,h0,s0,v1,c1,f1,u1,h1,s1,l0,l1,l2,eno,eslot,escore}=vectors[i];
   start=1;@(posedge clk);#1;start=0;cycles=0;
   while(!done && cycles<400) begin @(posedge clk);#1;cycles=cycles+1;end
   if(!done || no_path!==eno || (!eno && (route_valid!==1 || slot!==eslot || score!==escore)) || (eno && route_valid!==0)) begin
    $display("MISMATCH id=%0d done=%b no=%b/%b valid=%b slot=%0d/%0d score=%0d/%0d",i,done,no_path,eno,route_valid,slot,eslot,score,escore);errors=errors+1;
   end
   @(posedge clk);#1;
  end
  if(errors==0) $display("P5_B4_HOST_VECTORS=519_OF_519_EXACT_PASS");
  else begin $display("P5_B4_HOST_VECTORS=FAIL errors=%0d",errors);$fatal;end
  $finish;
 end
endmodule
