`timescale 1ns / 1ps

import graph_pkg::*;

module agg_max#(
    parameter int INPUT_DIM = INPUT_DIM_1,
    parameter int OUTPUT_DIM = OUTPUT_DIM_1
)(
    input  logic                        clk,
    input  logic                        reset,
    input  event_type                   in_event,
    input  edge_type    [MAX_EDGES-1:0] in_edges,
    input  logic [PRECISION-1:0] in_features [OUTPUT_DIM-1:0],
    output logic [PRECISION-1:0] out_feature [OUTPUT_DIM-1:0],
    output event_type                   out_event,
    output edge_type    [MAX_EDGES-1:0] out_edges

);

    logic [$clog2(MEMORY_OPS_NUM)-1 : 0] counter;
    
    always @(posedge clk) begin
        if (reset) begin
            counter <= 0;
        end else begin
            if (in_event.valid) begin
                counter <= 0;
            end
            if (counter < MEMORY_OPS_NUM-1) begin
                counter <= counter + 1;
            end
        end
    end
    
    genvar i;
    generate
        for (i = 0; i < OUTPUT_DIM; i++) begin : rows
            always @(posedge clk) begin
                if(reset || counter == MEMORY_OPS_NUM-1) begin
                    out_feature[i] <= '0;
                end else begin
                    out_feature[i] <= (in_features[i] > out_feature[i]) ? in_features[i] : out_feature[i];
                end
            end
        end
    endgenerate
    
    
    delay_module #(
        .N        ( F_WIDTH + T_WIDTH  + 1  ),
        .DELAY    ( MEMORY_OPS_NUM ) 
    ) delay_event (
        .clk   ( clk            ),
        .idata ( {in_event.t,  in_event.f, in_event.valid } ),
        .odata ( {out_event.t, out_event.f, out_event.valid} )
    );

    genvar j;
    generate
        for (j = 0; j < MAX_EDGES; j = j + 1) begin
            delay_module #(
                .N        ( F_WIDTH*2 + T_WIDTH*2  + 1  ),
                .DELAY    ( MEMORY_OPS_NUM  ) 
            ) delay_edges (
                .clk   ( clk            ),
                .idata ( {in_edges[j].t,  in_edges[j].f,  in_edges[j].dt,  in_edges[j].df,  in_edges[j].is_connected } ),
                .odata ( {out_edges[j].t, out_edges[j].f, out_edges[j].dt, out_edges[j].df, out_edges[j].is_connected} )
            );            
        end
    endgenerate 
    
    
    
    
endmodule