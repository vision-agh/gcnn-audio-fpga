
`timescale 1ns / 1ps

import graph_pkg::*;

module generate_graph #(
)( 
    input  logic                               clk,
    input  logic                               reset,
    input  logic      [T_WIDTH-1: 0]           t,
    input  logic      [F_WIDTH-1: 0]           f,
    input  logic                               is_valid,

    output event_type                          out_event,
    output edge_type  [MAX_EDGES-1 : 0]        out_edges,
    output logic      [N_WIDTH-1:0]            n,
    output logic                               empty
);

    event_type                    pos_item;
    edge_type   [MAX_EDGES-1 : 0] edges;

    edges_gen #(
    ) u_edges_gen (
        .clk           ( clk              ),
        .reset         ( reset            ),
        .t             ( t                ),
        .f             ( f                ),
        .is_valid      ( is_valid         ),
        .out_event     ( pos_item         ),
        .out_edges     ( edges            ),
        .n             ( n                ),
        .empty         ( empty            )
    );

    //not designed yet, path through module
    normalize #(
    ) u_normalize       (
        .clk            ( clk              ),
        .reset          ( reset            ),
        .in_event       ( pos_item         ),
        .in_edges       ( edges            ),
        .out_event      ( out_event        ),
        .out_edges      ( out_edges        )
    );

endmodule : generate_graph