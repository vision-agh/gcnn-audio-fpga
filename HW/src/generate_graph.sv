`timescale 1ns / 1ps

import graph_pkg::*;

module generate_graph #(
)( 
    input  logic                              clk,
    input  logic                              reset,
    input  logic            [T_WIDTH-1: 0]    t,
    input  logic            [F_WIDTH-1: 0]    f,
    input  logic                              is_valid,

    output event_type                         out_event,
    output edge_type        [MAX_EDGES-1 : 0] out_edges,
    output logic            [T_WIDTH-1:0]     t_feature,
    output logic            [F_WIDTH-1:0]     f_feature,
    
    output logic            [N_WIDTH-1:0]     n,
    output logic                              empty
);

    graph_event_type                    event_to_normalize;
    graph_edge_type   [MAX_EDGES-1 : 0] edges_to_normalize;

    logic             [T_WIDTH-1 : 0]   t_feature_to_normalize;
    logic             [F_WIDTH-1 : 0]   f_feature_to_normalize;

    edges_gen #(
    ) u_edges_gen (
        .clk           ( clk                    ),
        .reset         ( reset                  ),
        .t             ( t                      ),
        .f             ( f                      ),
        .is_valid      ( is_valid               ),
        .out_event     ( event_to_normalize     ),
        .out_edges     ( edges_to_normalize     ),
        .t_feature     ( t_feature_to_normalize ),
        .f_feature     ( f_feature_to_normalize ),
        .n             ( n                      ),
        .empty         ( empty                  )
    );
    
// for now path through module 
    normalize #(
    ) u_normalize       (
        .clk            ( clk                    ),
        .reset          ( reset                  ),
        .in_event       ( event_to_normalize     ),
        .in_edges       ( edges_to_normalize     ),
        .in_t_feature   ( t_feature_to_normalize ),
        .in_f_feature   ( f_feature_to_normalize ),
        .out_event      ( out_event              ),
        .out_edges      ( out_edges              ),
        .out_t_feature  ( t_feature              ),
        .out_f_feature  ( f_feature              )
    );

endmodule