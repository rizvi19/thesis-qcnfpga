`timescale 1ns / 1ps
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
