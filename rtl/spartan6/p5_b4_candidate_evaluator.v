`timescale 1ns / 1ps

module p5_b4_candidate_evaluator (
    input  wire        clk,
    input  wire        rst,
    input  wire        start,
    output wire        ready,
    input  wire        c0_valid,
    input  wire [31:0] c0_cost,
    input  wire [15:0] c0_fidelity,
    input  wire [31:0] c0_utilization,
    input  wire [2:0]  c0_hops,
    input  wire [1:0]  c0_slot,
    input  wire        c1_valid,
    input  wire [31:0] c1_cost,
    input  wire [15:0] c1_fidelity,
    input  wire [31:0] c1_utilization,
    input  wire [2:0]  c1_hops,
    input  wire [1:0]  c1_slot,
    input  wire [1:0]  lambda0,
    input  wire [1:0]  lambda1,
    input  wire [1:0]  lambda2,
    output reg         done,
    output reg         route_valid,
    output reg         no_path,
    output reg  [1:0]  selected_slot,
    output reg  [17:0] selected_score
);
    localparam S_IDLE=3'd0, S_PREP=3'd1, S_SCALE=3'd2,
               S_ROUND=3'd3, S_DIV_TEST=3'd4,
               S_DIV_COMMIT=3'd5, S_SCORE=3'd6, S_DONE=3'd7;
    reg [2:0] state;
    reg [1:0] objective;
    reg [15:0] n00, n01, n02, n10, n11, n12;
    reg high_is_c1;
    reg [48:0] dividend_shift, quotient;
    reg [33:0] remainder;
    reg [33:0] remainder_trial;
    reg [31:0] difference_reg;
    reg [47:0] scaled_difference_reg;
    reg subtract_needed;
    reg [32:0] divisor;
    reg [5:0] div_count;

    reg v0, v1;
    reg [31:0] cost0, cost1, util0, util1;
    reg [15:0] fid0, fid1;
    reg [2:0] hops0, hops1;
    reg [1:0] slot0, slot1, lam0, lam1, lam2;

    wire [31:0] obj0 = (objective==0) ? cost0 :
                       (objective==1) ? {16'd0,(16'hffff-fid0)} : util0;
    wire [31:0] obj1 = (objective==0) ? cost1 :
                       (objective==1) ? {16'd0,(16'hffff-fid1)} : util1;
    wire [31:0] difference = (obj0 > obj1) ? (obj0-obj1) : (obj1-obj0);
    wire [32:0] range_plus_one = {1'b0,difference} + 33'd1;

    function [17:0] weighted;
        input [15:0] n; input [1:0] l;
        begin case(l)
          0: weighted=0; 1: weighted={2'b0,n};
          2: weighted={1'b0,n,1'b0};
          default: weighted={2'b0,n}+{1'b0,n,1'b0};
        endcase end
    endfunction
    wire [17:0] p00=weighted(n00,lam0), p01=weighted(n01,lam1), p02=weighted(n02,lam2);
    wire [17:0] p10=weighted(n10,lam0), p11=weighted(n11,lam1), p12=weighted(n12,lam2);
    wire [17:0] score0=(p00>=p01 && p00>=p02)?p00:((p01>=p02)?p01:p02);
    wire [17:0] score1=(p10>=p11 && p10>=p12)?p10:((p11>=p12)?p11:p12);
    wire c0_wins = (score0 < score1) ||
                   ((score0 == score1) && ((cost0 < cost1) ||
                   ((cost0 == cost1) && ((hops0 < hops1) ||
                   ((hops0 == hops1) && (slot0 <= slot1))))));

    wire [33:0] rem_shift = {remainder[32:0],dividend_shift[48]};
    wire rem_ge = rem_shift >= {1'b0,divisor};
    assign ready = (state == S_IDLE);

    always @(posedge clk) begin
        if (rst) begin
            state<=S_IDLE; done<=0; route_valid<=0; no_path<=0;
            selected_slot<=0; selected_score<=0;
        end else begin
            done<=0; route_valid<=0;
            case (state)
                S_IDLE: if (start) begin
                    v0<=c0_valid; v1<=c1_valid; cost0<=c0_cost; cost1<=c1_cost;
                    fid0<=c0_fidelity; fid1<=c1_fidelity;
                    util0<=c0_utilization; util1<=c1_utilization;
                    hops0<=c0_hops; hops1<=c1_hops; slot0<=c0_slot; slot1<=c1_slot;
                    lam0<=lambda0; lam1<=lambda1; lam2<=lambda2;
                    n00<=0; n01<=0; n02<=0; n10<=0; n11<=0; n12<=0;
                    no_path<=0; objective<=0; state<=S_PREP;
                end
                S_PREP: begin
                    if (!v0 && !v1) begin no_path<=1; state<=S_DONE; end
                    else if (!v0 || !v1) state<=S_SCORE;
                    else if (obj0 == obj1) begin
                        if (objective==2) state<=S_SCORE;
                        else objective<=objective+1'b1;
                    end else begin
                        high_is_c1 <= (obj1 > obj0);
                        difference_reg <= difference;
                        divisor <= range_plus_one;
                        state <= S_SCALE;
                    end
                end
                S_SCALE: begin
                    scaled_difference_reg <=
                        ({16'd0,difference_reg} << 16) -
                        {16'd0,difference_reg};
                    state <= S_ROUND;
                end
                S_ROUND: begin
                    dividend_shift <=
                        {1'b0,scaled_difference_reg} +
                        ({16'd0,divisor} >> 1);
                    quotient <= 0;
                    remainder <= 0;
                    div_count <= 0;
                    state <= S_DIV_TEST;
                end
                S_DIV_TEST: begin
                    dividend_shift <= {dividend_shift[47:0],1'b0};
                    remainder_trial <= rem_shift;
                    subtract_needed <= rem_ge;
                    state <= S_DIV_COMMIT;
                end
                S_DIV_COMMIT: begin
                    remainder <= subtract_needed ?
                                 (remainder_trial-{1'b0,divisor}) : remainder_trial;
                    quotient <= {quotient[47:0],subtract_needed};
                    if (div_count==48) begin
                        if (high_is_c1) begin
                            if(objective==0) n10<={quotient[14:0],subtract_needed};
                            else if(objective==1) n11<={quotient[14:0],subtract_needed};
                            else n12<={quotient[14:0],subtract_needed};
                        end else begin
                            if(objective==0) n00<={quotient[14:0],subtract_needed};
                            else if(objective==1) n01<={quotient[14:0],subtract_needed};
                            else n02<={quotient[14:0],subtract_needed};
                        end
                        if(objective==2) state<=S_SCORE;
                        else begin objective<=objective+1'b1; state<=S_PREP; end
                    end else begin div_count<=div_count+1'b1; state<=S_DIV_TEST; end
                end
                S_SCORE: begin
                    no_path<=0; route_valid<=1;
                    if(v0 && !v1) begin selected_slot<=slot0; selected_score<=0; end
                    else if(v1 && !v0) begin selected_slot<=slot1; selected_score<=0; end
                    else if(c0_wins) begin selected_slot<=slot0; selected_score<=score0; end
                    else begin selected_slot<=slot1; selected_score<=score1; end
                    state<=S_DONE;
                end
                S_DONE: begin done<=1; route_valid<=!no_path; state<=S_IDLE; end
                default: state<=S_IDLE;
            endcase
        end
    end
endmodule
