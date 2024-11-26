`timescale 1ns / 1ps

import graph_pkg::*;

module average #(
    parameter int OUTPUT_DIM = OUTPUT_DIM_1
)(
    input  logic                        clk,
    input  logic                        reset,
    input  logic                        is_valid,
    input  event_type                   in_event,
    input  edge_type    [MAX_EDGES-1:0] in_edges,
    input  logic [PRECISION-1:0] in_features [OUTPUT_DIM-1:0],
    input  logic        [N_WIDTH-1 : 0] n,
    input  logic                        empty,
    output logic [PRECISION*2-1:0] out_feature,
    output logic                        out_valid

);
    logic [PRECISION-1:0] temp_feature [OUTPUT_DIM-1:0];
    logic [PRECISION*2+2-1:0] dividend_feature;  
    logic [$clog2(OUTPUT_DIM)-1 : 0] counter;
    logic divisor_tvalid;
    
    always @(posedge clk) begin
        if (reset) begin
            counter <= 0;
            divisor_tvalid <= 0;
        end else begin
            if (empty && counter != OUTPUT_DIM-1) begin
                counter <= counter + 1;
                divisor_tvalid <= 1;
            end else if (counter == OUTPUT_DIM-1) begin
                counter <= counter;
                divisor_tvalid <= 0;
            end else begin
                counter <= 0;
                divisor_tvalid <= 0;
            end
        end
    end
       
    always @(posedge clk) begin
        if(reset) begin
            dividend_feature <='0;
        end else begin
            dividend_feature <= temp_feature[counter];
        end 
    end
    
    genvar i;
    generate for(i=0;i<OUTPUT_DIM; i++) begin
        always @(posedge clk) begin
            if(reset) begin
                    temp_feature[i] <= '0; 
            end else begin
                if(in_event.valid) begin
                    temp_feature[i] <= temp_feature[i] + in_features[i]; 
                end
            end     
        end
        end
    endgenerate
    
    div_gen_0 divider (
        .aclk (clk),
        .s_axis_divisor_tdata ( n),
        .s_axis_divisor_tvalid ( divisor_tvalid),
        .s_axis_dividend_tdata(dividend_feature),
        .s_axis_dividend_tvalid ( divisor_tvalid),
        .m_axis_dout_tdata ( out_feature ),//32
        .m_axis_dout_tvalid ( out_valid)
    );
    endmodule