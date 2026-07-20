`timescale 1ns / 1ps
module p6_nexys3_campaign_common #(
 parameter [2:0] POLICY_MODE=3'd0
)(
 input wire clk_100mhz,input wire btn_reset,
 output wire led_heartbeat,output wire led_reset,
 output reg [7:0] seg_n,output reg [3:0] an_n,
 output wire uart_tx
);
wire campaign_done;
wire [6:0] records_completed;
wire [7:0] pass_count;
wire [15:0] error_count;
reg [17:0] scan;
reg [3:0] digit;
wire [3:0] ones=records_completed%10;
wire [3:0] tens=(records_completed/10)%10;

p6_physical_campaign_core #(
 .POLICY_MODE(POLICY_MODE),.CLK_HZ(100000000),.UART_BAUD(115200)
) campaign(
 .clk(clk_100mhz),.rst(btn_reset),.uart_tx(uart_tx),
 .campaign_done(campaign_done),.records_completed(records_completed),
 .pass_count(pass_count),.error_count(error_count));

assign led_heartbeat=campaign_done && (error_count==0) && (pass_count==84);
assign led_reset=(error_count!=0);

always @(posedge clk_100mhz) scan<=scan+1'b1;
always @* begin
 an_n=4'b1111;
 case(scan[17:16])
  2'd0:begin an_n=4'b1110;digit=ones;end
  2'd1:begin an_n=4'b1101;digit=tens;end
  2'd2:begin an_n=4'b1011;digit=4'd0;end
  default:begin an_n=4'b0111;digit={1'b0,POLICY_MODE};end
 endcase
 case(digit)
  0:seg_n=8'b11000000;1:seg_n=8'b11111001;
  2:seg_n=8'b10100100;3:seg_n=8'b10110000;
  4:seg_n=8'b10011001;5:seg_n=8'b10010010;
  6:seg_n=8'b10000010;7:seg_n=8'b11111000;
  8:seg_n=8'b10000000;9:seg_n=8'b10010000;
  default:seg_n=8'b11111111;
 endcase
end
endmodule

module p6_nexys3_h0(
 input wire clk_100mhz,input wire btn_reset,
 output wire led_heartbeat,output wire led_reset,
 output wire [7:0] seg_n,output wire [3:0] an_n,output wire uart_tx);
p6_nexys3_campaign_common #(.POLICY_MODE(3'd0)) u(
 .clk_100mhz(clk_100mhz),.btn_reset(btn_reset),.led_heartbeat(led_heartbeat),
 .led_reset(led_reset),.seg_n(seg_n),.an_n(an_n),.uart_tx(uart_tx));endmodule
module p6_nexys3_h1(
 input wire clk_100mhz,input wire btn_reset,
 output wire led_heartbeat,output wire led_reset,
 output wire [7:0] seg_n,output wire [3:0] an_n,output wire uart_tx);
p6_nexys3_campaign_common #(.POLICY_MODE(3'd1)) u(
 .clk_100mhz(clk_100mhz),.btn_reset(btn_reset),.led_heartbeat(led_heartbeat),
 .led_reset(led_reset),.seg_n(seg_n),.an_n(an_n),.uart_tx(uart_tx));endmodule
module p6_nexys3_h2(
 input wire clk_100mhz,input wire btn_reset,
 output wire led_heartbeat,output wire led_reset,
 output wire [7:0] seg_n,output wire [3:0] an_n,output wire uart_tx);
p6_nexys3_campaign_common #(.POLICY_MODE(3'd2)) u(
 .clk_100mhz(clk_100mhz),.btn_reset(btn_reset),.led_heartbeat(led_heartbeat),
 .led_reset(led_reset),.seg_n(seg_n),.an_n(an_n),.uart_tx(uart_tx));endmodule
module p6_nexys3_h3(
 input wire clk_100mhz,input wire btn_reset,
 output wire led_heartbeat,output wire led_reset,
 output wire [7:0] seg_n,output wire [3:0] an_n,output wire uart_tx);
p6_nexys3_campaign_common #(.POLICY_MODE(3'd3)) u(
 .clk_100mhz(clk_100mhz),.btn_reset(btn_reset),.led_heartbeat(led_heartbeat),
 .led_reset(led_reset),.seg_n(seg_n),.an_n(an_n),.uart_tx(uart_tx));endmodule
module p6_nexys3_h4(
 input wire clk_100mhz,input wire btn_reset,
 output wire led_heartbeat,output wire led_reset,
 output wire [7:0] seg_n,output wire [3:0] an_n,output wire uart_tx);
p6_nexys3_campaign_common #(.POLICY_MODE(3'd4)) u(
 .clk_100mhz(clk_100mhz),.btn_reset(btn_reset),.led_heartbeat(led_heartbeat),
 .led_reset(led_reset),.seg_n(seg_n),.an_n(an_n),.uart_tx(uart_tx));endmodule
