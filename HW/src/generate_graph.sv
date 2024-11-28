
`timescale 1ns / 1ps

import graph_pkg::*;

module generate_graph #(
)( 
    input  logic                              clk,
    input  logic                              reset,
    input  logic            [T_WIDTH-1: 0]    t,
    input  logic            [F_WIDTH-1: 0]    f,
    input  logic                              is_valid,
    
    // for debug output of edges_gen
    output graph_event_type                   event_to_normalize,
    output graph_edge_type  [MAX_EDGES-1 : 0] edges_to_normalize,
    output logic            [T_WIDTH-1:0]     t_feature_to_normalize,
    output logic            [F_WIDTH-1:0]     f_feature_to_normalize,

// if you don't simulate the result comment use below and [here]
//    output graph_event_type                   out_event,
//    output graph_edge_type  [MAX_EDGES-1 : 0] out_edges,
//    output logic            [T_WIDTH-1:0]     t_feature,
//    output logic            [F_WIDTH-1:0]     f_features,
    
    output logic            [N_WIDTH-1:0]     n,
    output logic                              empty
);

    graph_event_type                    event_to_normalize;
    graph_edge_type   [MAX_EDGES-1 : 0] edges_to_normalize;

// [here]
//    logic             [T_WIDTH-1 : 0]   t_feature_to_normalize;
//    logic             [F_WIDTH-1 : 0]   f_feature_to_normalize;

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
//    normalize #(
//    ) u_normalize       (
//        .clk            ( clk                    ),
//        .reset          ( reset                  ),
//        .in_event       ( event_to_normalize     ),
//        .in_edges       ( edges_to_normalize     ),
//        .in_t_features  ( t_feature_to_normalize ),
//        .in_f_features  ( f_feature_to_normalize ),
//        .out_event      ( out_event              ),
//        .out_edges      ( out_edges              ),
//        .out_t_features ( t_features             ),
//        .out_f_features ( f_features             )
//    );

endmodule