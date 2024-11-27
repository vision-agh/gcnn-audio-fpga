`timescale 1ns / 1ps

import graph_pkg::*;

module normalize#(

)(
    input     logic                         clk,
    input     logic                         reset,
    input     graph_event_type                    in_event,
    input     graph_edge_type   [MAX_EDGES-1 : 0] in_edges,
    input     logic [T_WIDTH-1:0]           in_t_features,
    input     logic [F_WIDTH-1:0]           in_f_features,
    output    event_type                    out_event,
    output    edge_type   [MAX_EDGES-1 : 0] out_edges,
    output    logic [T_WIDTH-1:0]           out_t_features,
    output    logic [F_WIDTH-1:0]           out_f_features
);
    
    //path through module
    
    event_type temp_event;
    logic [T_WIDTH-1:0] temp_t_features;
    logic [F_WIDTH-1:0] temp_f_features;
    
    assign temp_t_features = in_t_features;
    assign temp_f_features = in_f_features;
    assign out_t_features = temp_t_features;
    assign out_f_features = temp_f_features;
    
    assign temp_event.t = in_event.valid ? in_event.t : '0;
    assign temp_event.f = in_event.valid ? in_event.f  : '0;
    assign temp_event.valid = in_event.valid;
    
    assign out_event.t = temp_event.valid ? temp_event.t : '0;
    assign out_event.f = temp_event.valid ? temp_event.f: '0;
    assign out_event.valid = temp_event.valid;
    
    
    edge_type [MAX_EDGES-1 : 0] temp_edge;
    
    genvar i;
    
    generate
        for (i=0;i<MAX_EDGES;i=i+1) begin
                assign temp_edge[i].dt           = in_edges[i].is_connected ? in_edges[i].dt : '0;
                assign temp_edge[i].is_connected = in_edges[i].is_connected;
  
                assign out_edges[i].dt           = temp_edge[i].is_connected ? temp_edge[i].dt: '0;
                assign out_edges[i].is_connected = temp_edge[i].is_connected;
            end           
    endgenerate
    
    
endmodule
