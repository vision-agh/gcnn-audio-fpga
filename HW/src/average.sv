`timescale 1ns / 1ps

import graph_pkg::*;

module average #(
    parameter int OUTPUT_DIM = OUTPUT_DIM_4
)(
    input  logic                                   clk,
    input  logic                                   reset,
    input  logic                                   in_event_valid,
    input  logic      [PRECISION-1:0]              in_features [OUTPUT_DIM-1:0],
    input  logic      [N_WIDTH-1 : 0]              n,
    input  logic                                   empty,
    input  logic                                   data_input_finished,
    output logic      [$clog2(OUTPUT_DIM)-1: 0]    out_address, 
    output logic      [PRECISION-1:0]              out_feature,
    output logic                                   out_valid

);
    logic [PRECISION+T_WIDTH-1:0]    temp_feature [OUTPUT_DIM-1:0];
    logic [PRECISION+T_WIDTH-1:0]    dividend_feature;  
    logic [$clog2(OUTPUT_DIM)-1:0]   counter;
    logic                            divisor_tvalid;
    logic [OUTPUT_DIM-1:0]           temp_out_feature;
    logic [N_WIDTH-1:0]              n_counter;
    logic                            done;
    logic                            data_input_finished_reg;
    
    always @(posedge clk) begin
        if(reset) begin
            data_input_finished_reg <= 0;
        end else if(data_input_finished) begin
            data_input_finished_reg <= 1;
        end else begin
            data_input_finished_reg <= data_input_finished_reg;
        end
    end
    
    assign done = empty && n == n_counter && data_input_finished_reg;
    
    always @(posedge clk) begin
        if(reset) begin
            n_counter <= 0;
        end else begin
            if(in_event_valid) begin
                n_counter <= n_counter + 1;
            end else begin
                n_counter <= n_counter;
            end
        end    
    end
    
    logic done_reg;
    
    always @(posedge clk) begin
        if(reset) begin
            done_reg <= 0;
        end else begin
            done_reg <= done;
        end
    end
    
    always @(posedge clk) begin
        if (reset) begin
            counter <= 0;
            divisor_tvalid <= 0;
        end else begin
            if (done && !done_reg) begin
                counter <= 0;
                divisor_tvalid <= 1;
            end else if (counter == OUTPUT_DIM-1) begin
                counter <= counter;
                divisor_tvalid <= 0;
            end else if (done && done_reg) begin
                counter <= counter + 1;
                divisor_tvalid <= 1;
            end
        end
    end
    
    assign dividend_feature = temp_feature[counter];
    
    genvar i;
    generate for(i=0;i<OUTPUT_DIM; i++) begin
        always @(posedge clk) begin
            if(reset) begin
                    temp_feature[i] <= '0; 
            end else begin
                if(in_event_valid) begin
                    temp_feature[i] <= temp_feature[i] + in_features[i]; 
                end
            end     
        end
        end
    endgenerate
    
    assign out_feature = temp_out_feature[30:2];
    
    always @(posedge clk) begin
        if(reset) begin
            out_address <= '0;
        end else begin
            if(out_valid) begin
                out_address <= out_address + 1;
            end else begin
                out_address <= '0;
            end
        end
    end
    
    
    div_gen_0 divider ( //1clock latency
        .aclk (clk),
        .s_axis_divisor_tdata   ( n                ),//14bit
        .s_axis_divisor_tvalid  ( divisor_tvalid   ),
        .s_axis_dividend_tdata  ( dividend_feature ),//29bit(21 + 8)
        .s_axis_dividend_tvalid ( divisor_tvalid   ),
        .m_axis_dout_tdata      ( temp_out_feature ),//30~2, 1~0 fixed point
        .m_axis_dout_tvalid     ( out_valid        )
    );
endmodule
