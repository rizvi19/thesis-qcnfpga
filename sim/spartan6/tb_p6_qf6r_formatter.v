`timescale 1ns / 1ps
module tb_p6_qf6r_formatter;
localparam RECORDS=420;
localparam TOTAL_BYTES=18480;
reg clk,rst,start;
wire ready,done,byte_valid;
wire [7:0] byte_data;
reg [15:0] test_mem[0:RECORDS-1];
reg [2:0] policy_mem[0:RECORDS-1];
reg [7:0] state_mem[0:RECORDS-1];
reg [1:0] profile_mem[0:RECORDS-1];
reg [7:0] path_mem[0:RECORDS-1];
reg [17:0] score_mem[0:RECORDS-1];
reg [15:0] fid_mem[0:RECORDS-1];
reg [15:0] cycles_mem[0:RECORDS-1];
reg [2:0] status_mem[0:RECORDS-1];
reg [7:0] expected[0:TOTAL_BYTES-1];
integer rec,byte_count,errors;

p6_qf6r_formatter dut(
 .clk(clk),.rst(rst),.start(start),.ready(ready),.done(done),
 .test_id(test_mem[rec]),.policy_id(policy_mem[rec]),
 .state_id(state_mem[rec]),.profile_id(profile_mem[rec]),
 .selected_path(path_mem[rec]),.score(score_mem[rec]),
 .bottleneck_fidelity(fid_mem[rec]),.cycles(cycles_mem[rec]),
 .status(status_mem[rec]),.uart_ready(1'b1),
 .byte_valid(byte_valid),.byte_data(byte_data));

always #5 clk=~clk;

always @(posedge clk) begin
 if(!rst && byte_valid) begin
  if(byte_count>=TOTAL_BYTES) begin
   $display("FORMATTER_EXTRA_BYTE actual=%02x",byte_data);
   errors=errors+1;
  end else if(byte_data!==expected[byte_count]) begin
   $display("FORMATTER_BYTE_FAIL index=%0d actual=%02x expected=%02x",
            byte_count,byte_data,expected[byte_count]);
   errors=errors+1;
  end
  byte_count=byte_count+1;
 end
end

initial begin
 $readmemh("results/nexys3/p6_step3_formatter_repair/vectors/test_id.mem",test_mem);
 $readmemh("results/nexys3/p6_step3_formatter_repair/vectors/policy_id.mem",policy_mem);
 $readmemh("results/nexys3/p6_step3_formatter_repair/vectors/state_id.mem",state_mem);
 $readmemh("results/nexys3/p6_step3_formatter_repair/vectors/profile_id.mem",profile_mem);
 $readmemh("results/nexys3/p6_step3_formatter_repair/vectors/selected_path.mem",path_mem);
 $readmemh("results/nexys3/p6_step3_formatter_repair/vectors/score.mem",score_mem);
 $readmemh("results/nexys3/p6_step3_formatter_repair/vectors/bottleneck_fidelity.mem",fid_mem);
 $readmemh("results/nexys3/p6_step3_formatter_repair/vectors/cycles.mem",cycles_mem);
 $readmemh("results/nexys3/p6_step3_formatter_repair/vectors/status.mem",status_mem);
 $readmemh("results/nexys3/p6_step3_formatter_repair/vectors/expected_bytes.mem",expected);

 clk=0;rst=1;start=0;rec=0;byte_count=0;errors=0;
 repeat(5) @(posedge clk);
 rst=0;
 repeat(2) @(posedge clk);

 for(rec=0;rec<RECORDS;rec=rec+1) begin
  while(!ready) @(posedge clk);
  @(negedge clk);start=1;
  @(posedge clk);
  @(negedge clk);start=0;
  while(!done) @(posedge clk);
 end

 while(byte_count<TOTAL_BYTES) @(posedge clk);
 repeat(4) @(posedge clk);

 if(errors==0 && byte_count==TOTAL_BYTES)
  $display("P6_QF6R_FORMATTER=18480_OF_18480_BYTES_PASS");
 else
  $display("P6_QF6R_FORMATTER=FAIL bytes=%0d errors=%0d",
           byte_count,errors);
 $finish;
end

initial begin
 #100000000;
 $display("P6_QF6R_FORMATTER=FAIL_TIMEOUT");
 $finish;
end
endmodule
