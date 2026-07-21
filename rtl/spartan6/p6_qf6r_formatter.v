`timescale 1ns / 1ps

// P6 QF6R v1 formatter.
//
// Exact output:
// QF6R,1,TTTT,P,SSS,R,PPP,CCCCCC,FFFFF,LLL,E\r\n
//
// Every record is 44 bytes. Decimal conversion uses an iterative
// shift-add-3 binary-to-BCD conversion: 18 short pipeline steps per field.
// This removes the previous single-cycle /10 and %10 critical path.
// Formatter and UART time remain outside the synchronous kernel counter.
module p6_qf6r_formatter (
    input  wire        clk,
    input  wire        rst,
    input  wire        start,
    output wire        ready,
    output reg         done,

    input  wire [15:0] test_id,
    input  wire [2:0]  policy_id,
    input  wire [7:0]  state_id,
    input  wire [1:0]  profile_id,
    input  wire [7:0]  selected_path,
    input  wire [17:0] score,
    input  wire [15:0] bottleneck_fidelity,
    input  wire [15:0] cycles,
    input  wire [2:0]  status,

    input  wire        uart_ready,
    output wire        byte_valid,
    output reg  [7:0]  byte_data
);

    localparam S_IDLE  = 3'd0;
    localparam S_LOAD  = 3'd1;
    localparam S_SHIFT = 3'd2;
    localparam S_STORE = 3'd3;
    localparam S_SEND  = 3'd4;

    reg [2:0] state;
    reg [3:0] field_index;
    reg [4:0] bit_count;
    reg [5:0] byte_index;

    reg [17:0] binary_reg;
    reg [23:0] bcd_reg;
    reg [23:0] bcd_adjusted;
    reg [3:0] digits [0:26];

    reg [15:0] test_id_r;
    reg [2:0]  policy_id_r;
    reg [7:0]  state_id_r;
    reg [1:0]  profile_id_r;
    reg [7:0]  selected_path_r;
    reg [17:0] score_r;
    reg [15:0] fidelity_r;
    reg [15:0] cycles_r;
    reg [2:0]  status_r;

    integer n;

    assign ready = (state == S_IDLE);
    assign byte_valid = (state == S_SEND) && uart_ready;

    always @* begin
        bcd_adjusted = bcd_reg;
        if (bcd_reg[3:0]   >= 5) bcd_adjusted[3:0]   = bcd_reg[3:0]   + 3;
        if (bcd_reg[7:4]   >= 5) bcd_adjusted[7:4]   = bcd_reg[7:4]   + 3;
        if (bcd_reg[11:8]  >= 5) bcd_adjusted[11:8]  = bcd_reg[11:8]  + 3;
        if (bcd_reg[15:12] >= 5) bcd_adjusted[15:12] = bcd_reg[15:12] + 3;
        if (bcd_reg[19:16] >= 5) bcd_adjusted[19:16] = bcd_reg[19:16] + 3;
        if (bcd_reg[23:20] >= 5) bcd_adjusted[23:20] = bcd_reg[23:20] + 3;
    end

    always @* begin
        byte_data = 8'h00;
        case (byte_index)
          0: byte_data = "Q";
          1: byte_data = "F";
          2: byte_data = "6";
          3: byte_data = "R";
          4: byte_data = ",";
          5: byte_data = "1";
          6: byte_data = ",";
          7: byte_data = 8'h30 + digits[0];
          8: byte_data = 8'h30 + digits[1];
          9: byte_data = 8'h30 + digits[2];
         10: byte_data = 8'h30 + digits[3];
         11: byte_data = ",";
         12: byte_data = 8'h30 + digits[4];
         13: byte_data = ",";
         14: byte_data = 8'h30 + digits[5];
         15: byte_data = 8'h30 + digits[6];
         16: byte_data = 8'h30 + digits[7];
         17: byte_data = ",";
         18: byte_data = 8'h30 + digits[8];
         19: byte_data = ",";
         20: byte_data = 8'h30 + digits[9];
         21: byte_data = 8'h30 + digits[10];
         22: byte_data = 8'h30 + digits[11];
         23: byte_data = ",";
         24: byte_data = 8'h30 + digits[12];
         25: byte_data = 8'h30 + digits[13];
         26: byte_data = 8'h30 + digits[14];
         27: byte_data = 8'h30 + digits[15];
         28: byte_data = 8'h30 + digits[16];
         29: byte_data = 8'h30 + digits[17];
         30: byte_data = ",";
         31: byte_data = 8'h30 + digits[18];
         32: byte_data = 8'h30 + digits[19];
         33: byte_data = 8'h30 + digits[20];
         34: byte_data = 8'h30 + digits[21];
         35: byte_data = 8'h30 + digits[22];
         36: byte_data = ",";
         37: byte_data = 8'h30 + digits[23];
         38: byte_data = 8'h30 + digits[24];
         39: byte_data = 8'h30 + digits[25];
         40: byte_data = ",";
         41: byte_data = 8'h30 + digits[26];
         42: byte_data = 8'h0d;
         43: byte_data = 8'h0a;
         default: byte_data = 8'h00;
        endcase
    end

    always @(posedge clk) begin
        if (rst) begin
            state <= S_IDLE;
            field_index <= 0;
            bit_count <= 0;
            byte_index <= 0;
            binary_reg <= 0;
            bcd_reg <= 0;
            done <= 0;
            test_id_r <= 0;
            policy_id_r <= 0;
            state_id_r <= 0;
            profile_id_r <= 0;
            selected_path_r <= 0;
            score_r <= 0;
            fidelity_r <= 0;
            cycles_r <= 0;
            status_r <= 0;
            for (n = 0; n < 27; n = n + 1)
                digits[n] <= 0;
        end else begin
            done <= 0;
            case (state)
              S_IDLE: begin
                  if (start) begin
                      test_id_r <= test_id;
                      policy_id_r <= policy_id;
                      state_id_r <= state_id;
                      profile_id_r <= profile_id;
                      selected_path_r <= selected_path;
                      score_r <= score;
                      fidelity_r <= bottleneck_fidelity;
                      cycles_r <= cycles;
                      status_r <= status;
                      field_index <= 0;
                      byte_index <= 0;
                      state <= S_LOAD;
                  end
              end

              S_LOAD: begin
                  bcd_reg <= 0;
                  bit_count <= 0;
                  case (field_index)
                    0: binary_reg <= {2'd0, test_id_r};
                    1: binary_reg <= {15'd0, policy_id_r};
                    2: binary_reg <= {10'd0, state_id_r};
                    3: binary_reg <= {16'd0, profile_id_r};
                    4: binary_reg <= {10'd0, selected_path_r};
                    5: binary_reg <= score_r;
                    6: binary_reg <= {2'd0, fidelity_r};
                    7: binary_reg <= {2'd0, cycles_r};
                    default: binary_reg <= {15'd0, status_r};
                  endcase
                  state <= S_SHIFT;
              end

              S_SHIFT: begin
                  if (bit_count == 18) begin
                      state <= S_STORE;
                  end else begin
                      bcd_reg <= {bcd_adjusted[22:0], binary_reg[17]};
                      binary_reg <= {binary_reg[16:0], 1'b0};
                      bit_count <= bit_count + 1'b1;
                  end
              end

              S_STORE: begin
                  case (field_index)
                    0: begin
                        digits[0] <= bcd_reg[15:12];
                        digits[1] <= bcd_reg[11:8];
                        digits[2] <= bcd_reg[7:4];
                        digits[3] <= bcd_reg[3:0];
                    end
                    1: digits[4] <= bcd_reg[3:0];
                    2: begin
                        digits[5] <= bcd_reg[11:8];
                        digits[6] <= bcd_reg[7:4];
                        digits[7] <= bcd_reg[3:0];
                    end
                    3: digits[8] <= bcd_reg[3:0];
                    4: begin
                        digits[9] <= bcd_reg[11:8];
                        digits[10] <= bcd_reg[7:4];
                        digits[11] <= bcd_reg[3:0];
                    end
                    5: begin
                        digits[12] <= bcd_reg[23:20];
                        digits[13] <= bcd_reg[19:16];
                        digits[14] <= bcd_reg[15:12];
                        digits[15] <= bcd_reg[11:8];
                        digits[16] <= bcd_reg[7:4];
                        digits[17] <= bcd_reg[3:0];
                    end
                    6: begin
                        digits[18] <= bcd_reg[19:16];
                        digits[19] <= bcd_reg[15:12];
                        digits[20] <= bcd_reg[11:8];
                        digits[21] <= bcd_reg[7:4];
                        digits[22] <= bcd_reg[3:0];
                    end
                    7: begin
                        digits[23] <= bcd_reg[11:8];
                        digits[24] <= bcd_reg[7:4];
                        digits[25] <= bcd_reg[3:0];
                    end
                    default: digits[26] <= bcd_reg[3:0];
                  endcase

                  if (field_index == 8) begin
                      byte_index <= 0;
                      state <= S_SEND;
                  end else begin
                      field_index <= field_index + 1'b1;
                      state <= S_LOAD;
                  end
              end

              S_SEND: begin
                  if (uart_ready) begin
                      if (byte_index == 43) begin
                          done <= 1'b1;
                          state <= S_IDLE;
                      end else begin
                          byte_index <= byte_index + 1'b1;
                      end
                  end
              end

              default: state <= S_IDLE;
            endcase
        end
    end
endmodule
