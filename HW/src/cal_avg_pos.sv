`timescale 1ns / 1ps

import graph_pkg::*;

module cal_avg_pos #(
)( 
    input                                      clk,
    input                                      reset,
    input  graph_event_type                    in_event,
    input  graph_edge_type  [MAX_EDGES-1 : 0]  in_edges,
   
    output graph_event_type                    out_event,
    output graph_edge_type  [MAX_EDGES-1 : 0]  out_edges
);
    logic [T_WIDTH*MAX_EDGES-1 : 0] t_temp;
    logic [F_WIDTH*MAX_EDGES-1 : 0] f_temp;

    genvar i;
    generate
        for (i = 0; i < MAX_EDGES; i++) begin
            always @(posedge clk) begin
                
            end
            
            always @(posedge clk) begin

            end
        end
    endgenerate

endmodule