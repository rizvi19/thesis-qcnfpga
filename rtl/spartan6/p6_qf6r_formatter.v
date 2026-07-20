`timescale 1ns / 1ps
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
