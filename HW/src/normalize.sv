`timescale 1ns / 1ps

import graph_pkg::*;

module normalize#(

)(
    input     logic                         clk,
    input     logic                         reset,
    input     event_type                    in_event,
    input     edge_type   [MAX_EDGES-1 : 0] in_edges,
    output    event_type                    out_event,
    output    edge_type   [MAX_EDGES-1 : 0] out_edges
);
    logic signed [F_WIDTH-1 : 0] base_num = NUM_CHANNEL; 

    //implement normalization later
    //event normalization
    event_type temp_event;
    
    assign temp_event.t = in_event.valid ? in_event.t : '0;
//    assign temp_event.f = in_event.valid ? ((in_event.f <<< 1) - base_num) <<< (SCALE - 10)  : '0;
    assign temp_event.f = in_event.valid ? in_event.f  : '0;
//    assign temp_event.n = in_event.valid ? in_event.n  : '0;
    assign temp_event.valid = in_event.valid;
    
    assign out_event.t = temp_event.valid ? temp_event.t : '0;
    assign out_event.f = temp_event.valid ? temp_event.f: '0;
//    assign out_event.n = temp_event.valid ? temp_event.n: '0;
    assign out_event.valid = temp_event.valid;
    
    
    //edge normalization
    edge_type [MAX_EDGES-1 : 0] temp_edge;
    
    genvar i;
    
    generate
        for (i=0;i<MAX_EDGES;i=i+1) begin
                assign temp_edge[i].t            = in_edges[i].is_connected ? in_edges[i].t : '0;
//                assign temp_edge[i].f            = in_edges[i].is_connected ? (((in_edges[i].f <<< 1) - base_num) <<< (SCALE - 10)) : '0;
                assign temp_edge[i].f            = in_edges[i].is_connected ? in_edges[i].f : '0;
                assign temp_edge[i].dt           = in_edges[i].is_connected ? in_edges[i].dt : '0;
//                assign temp_edge[i].df           = in_edges[i].is_connected ? ((in_edges[i].df <<< 1) <<< (SCALE - 10)) : '0;
                assign temp_edge[i].df           = in_edges[i].is_connected ? in_edges[i].df : '0;
//                assign temp_edge[i].n            = in_edges[i].is_connected ? in_edges[i].n : '0;
                assign temp_edge[i].is_connected = in_edges[i].is_connected;
  
                assign out_edges[i].t            = temp_edge[i].is_connected ? temp_edge[i].t : '0;
                assign out_edges[i].f            = temp_edge[i].is_connected ? temp_edge[i].f: '0;
                assign out_edges[i].dt           = temp_edge[i].is_connected ? temp_edge[i].dt: '0;
                assign out_edges[i].df           = temp_edge[i].is_connected ? temp_edge[i].df: '0;
//                assign out_edges[i].n            = temp_edge[i].is_connected ? temp_edge[i].n : '0;
                assign out_edges[i].is_connected = temp_edge[i].is_connected;
            end           
    endgenerate
    
    
endmodule
