`timescale 1ns / 1ps

import graph_pkg::*;

module normalize#(

)(
    input     logic                                clk,
    input     logic                                reset,
    input     graph_event_type                     in_event,
    input     graph_edge_type   [MAX_EDGES-1 : 0]  in_edges,
    input     logic             [T_WIDTH-1:0]      in_t_feature,
    input     logic             [F_WIDTH-1:0]      in_f_feature,
    output    event_type                           out_event,
    output    edge_type         [MAX_EDGES-1 : 0]  out_edges,
    output    logic             [T_WIDTH-1:0]      out_t_feature,
    output    logic             [F_WIDTH-1:0]      out_f_feature
);
    
    //path through module
    
    assign out_t_feature  = in_t_feature;
    assign out_f_feature  = in_f_feature;
    
    assign out_event.t     = in_event.valid ? in_event.t : '0;
    assign out_event.f     = in_event.valid ? in_event.f  : '0;
    assign out_event.valid = in_event.valid;

    genvar i;
    generate
        for (i=0;i<MAX_EDGES;i=i+1) begin
                assign out_edges[i].dt           = in_edges[i].is_connected ? in_edges[i].dt : '0;
                assign out_edges[i].is_connected = in_edges[i].is_connected;
            end           
    endgenerate
    
    
endmodule
