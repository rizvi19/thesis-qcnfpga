`timescale 1ns / 1ps
module tb_p6_uart_byte_stream;
localparam TOTAL_BYTES=18480;
reg clk,rst,data_valid;
reg [7:0] data_byte;
wire ready,tx,busy;
reg [7:0] expected[0:TOTAL_BYTES-1];
integer send_index,rx_index,errors,bitn;
reg [7:0] rx_byte;

p5_b1_uart_tx #(.CLK_HZ(1000000),.BAUD(100000)) dut(
 .clk(clk),.rst(rst),.data_valid(data_valid),.data_byte(data_byte),
 .ready(ready),.tx(tx),.busy(busy));

always #500 clk=~clk;

task decode_byte;
begin
 repeat(5) @(posedge clk);
 if(tx!==1'b0) begin
   $display("UART_START_BIT_FAIL index=%0d",rx_index);
   errors=errors+1;
 end
 rx_byte=0;
 for(bitn=0;bitn<8;bitn=bitn+1) begin
   repeat(10) @(posedge clk);
   rx_byte[bitn]=tx;
 end
 repeat(10) @(posedge clk);
 if(tx!==1'b1) begin
   $display("UART_STOP_BIT_FAIL index=%0d",rx_index);
   errors=errors+1;
 end
 if(rx_byte!==expected[rx_index]) begin
   $display("UART_BYTE_FAIL index=%0d actual=%02x expected=%02x",
            rx_index,rx_byte,expected[rx_index]);
   errors=errors+1;
 end
 $write("%c",rx_byte);
 rx_index=rx_index+1;
end
endtask

always @(negedge tx) decode_byte;

initial begin
 $readmemh("results/nexys3/p6_step3_uart_transport/expected_bytes.mem",expected);
 clk=0;rst=1;data_valid=0;data_byte=0;
 send_index=0;rx_index=0;errors=0;
 repeat(5) @(posedge clk);
 rst=0;
 repeat(2) @(posedge clk);

 for(send_index=0;send_index<TOTAL_BYTES;send_index=send_index+1) begin
   while(!ready) @(posedge clk);
   @(negedge clk);
   data_byte=expected[send_index];
   data_valid=1;
   @(posedge clk);
   #1;
   @(negedge clk);
   data_valid=0;
 end

 while(rx_index<TOTAL_BYTES) @(posedge clk);
 repeat(20) @(posedge clk);

 if(errors==0)
   $display("P6_UART_BIT_LEVEL=18480_OF_18480_BYTES_PASS");
 else
   $display("P6_UART_BIT_LEVEL=FAIL errors=%0d",errors);
 $finish;
end

initial begin
 #3000000000;
 $display("P6_UART_BIT_LEVEL=FAIL_TIMEOUT");
 $finish;
end
endmodule
