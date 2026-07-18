`timescale 1ns / 1ps

module tb_rl_controller_exhaustive;
    reg clk, rst, start, input_valid, no_path_in;
    reg [15:0] min_key_occupancy_u16, bottleneck_fidelity_u16;
    reg [15:0] offered_request_load_u16, utilization_imbalance_u16;
    wire ready, busy, done, output_valid, invalid_state, stall, no_path_out;
    wire [7:0] state_id;
    wire [1:0] proposed_action, selected_action, dwell_count_sat;
    wire [17:0] profile_payload;
    wire switched;
    integer vector_file, scan_count, vector_count, decision_count, failure_count;
    integer cycle_i, rst_i, start_i, input_valid_i, no_path_i;
    integer key_i, fidelity_i, load_i, imbalance_i;
    integer ready_i, busy_i, done_i, output_valid_i, invalid_i, stall_i, no_path_out_i;
    integer state_id_i, proposed_i, selected_i, payload_i, switched_i, dwell_i;

    rl_controller dut (
        .clk(clk), .rst(rst), .start(start), .input_valid(input_valid), .no_path_in(no_path_in),
        .min_key_occupancy_u16(min_key_occupancy_u16), .bottleneck_fidelity_u16(bottleneck_fidelity_u16),
        .offered_request_load_u16(offered_request_load_u16), .utilization_imbalance_u16(utilization_imbalance_u16),
        .ready(ready), .busy(busy), .done(done), .output_valid(output_valid), .invalid_state(invalid_state),
        .stall(stall), .no_path_out(no_path_out), .state_id(state_id), .proposed_action(proposed_action),
        .selected_action(selected_action), .profile_payload(profile_payload), .switched(switched),
        .dwell_count_sat(dwell_count_sat)
    );
    always #5 clk = ~clk;
    task read_vector;
        begin
            scan_count = $fscanf(vector_file,
                "%d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d\n",
                cycle_i, rst_i, start_i, input_valid_i, no_path_i, key_i, fidelity_i, load_i, imbalance_i,
                ready_i, busy_i, done_i, output_valid_i, invalid_i, stall_i, no_path_out_i,
                state_id_i, proposed_i, selected_i, payload_i, switched_i, dwell_i);
        end
    endtask
    initial begin
        clk=0; rst=0; start=0; input_valid=0; no_path_in=0;
        min_key_occupancy_u16=0; bottleneck_fidelity_u16=0; offered_request_load_u16=0; utilization_imbalance_u16=0;
        vector_count=0; decision_count=0; failure_count=0;
        vector_file=$fopen("sim/rl/p4_exhaustive_vectors.txt","r");
        if(vector_file==0) begin $display("P4_EXHAUSTIVE_RTL_FAIL cannot_open_vector_file"); $finish; end
        read_vector;
        while(scan_count==22) begin
            @(negedge clk);
            rst=rst_i[0]; start=start_i[0]; input_valid=input_valid_i[0]; no_path_in=no_path_i[0];
            min_key_occupancy_u16=key_i[15:0]; bottleneck_fidelity_u16=fidelity_i[15:0];
            offered_request_load_u16=load_i[15:0]; utilization_imbalance_u16=imbalance_i[15:0];
            @(posedge clk); #1;
            if((ready!==ready_i[0])||(busy!==busy_i[0])||(done!==done_i[0])||
               (output_valid!==output_valid_i[0])||(invalid_state!==invalid_i[0])||(stall!==stall_i[0])||
               (no_path_out!==no_path_out_i[0])||(state_id!==state_id_i[7:0])||
               (proposed_action!==proposed_i[1:0])||(selected_action!==selected_i[1:0])||
               (profile_payload!==payload_i[17:0])||(switched!==switched_i[0])||
               (dwell_count_sat!==dwell_i[1:0])) begin
                failure_count=failure_count+1;
                $display("P4_EXHAUSTIVE_MISMATCH cycle=%0d",cycle_i);
            end
            if(output_valid===1'b1) decision_count=decision_count+1;
            vector_count=vector_count+1; read_vector;
        end
        $fclose(vector_file);
        if(scan_count!=-1) begin $display("P4_EXHAUSTIVE_RTL_FAIL malformed_vector_file scan=%0d",scan_count); $finish; end
        if(vector_count!=1509 || decision_count!=302) begin
            $display("P4_EXHAUSTIVE_RTL_FAIL vectors=%0d decisions=%0d",vector_count,decision_count); $finish;
        end
        if(failure_count!=0) begin $display("P4_EXHAUSTIVE_RTL_FAIL mismatches=%0d",failure_count); $finish; end
        $display("P4_EXHAUSTIVE_RTL_PASS vectors=%0d decisions=%0d mismatches=0",vector_count,decision_count);
        $finish;
    end
endmodule
