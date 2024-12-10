`timescale 1ns / 1ps

import graph_pkg::*;

module top #(
)( 
    input logic                                clk,
    input logic                                reset,
    input logic   [T_WIDTH-1: 0]               t, 
    input logic   [F_WIDTH-1: 0]               f, 
    input logic                                is_valid,
    input logic                                data_input_finished,
    output logic  [$clog2(OUTPUT_DIM_4)-1: 0]  out_address,                
    output logic  [PRECISION*2-1: 0]           out_feature,
    output logic                               out_valid
);

    event_type                event_to_u_agg_max1, event_to_u_agg_max2, event_to_u_agg_max3, event_to_u_agg_max4;
    edge_type [MAX_EDGES-1:0] edges_to_u_agg_max1, edges_to_u_agg_max2, edges_to_u_agg_max3, edges_to_u_agg_max4;
    
    event_type                event_to_feature_mem1, event_to_feature_mem2, event_to_feature_mem3, event_to_feature_mem4;
    edge_type [MAX_EDGES-1:0] edges_to_feature_mem1, edges_to_feature_mem2, edges_to_feature_mem3, edges_to_feature_mem4;
    
    event_type                event_to_u_conv1, event_to_u_conv2, event_to_u_conv3, event_to_u_conv4;
    edge_type [MAX_EDGES-1:0] edges_to_u_conv1, edges_to_u_conv2, edges_to_u_conv3, edges_to_u_conv4;

    generate_graph u_gen_graph (
        .clk        ( clk             ),
        .reset      ( reset           ),
        .t          ( t               ),
        .f          ( f               ),
        .is_valid   ( is_valid        ),
        .out_event  ( event_to_u_conv1 ),
        .out_edges  ( edges_to_u_conv1 ),
        .n          ( n                ),
        .empty      ( empty           )
    );
    
    // sequential_conv #(
    //     .INPUT_DIM  ( INPUT_DIM_1         ),
    //     .OUTPUT_DIM ( OUTPUT_DIM_1        )
    // ) u_conv1 (
    //     .clk        ( clk                 ),
    //     .reset      ( reset               ),
    //     .in_event   ( event_to_u_conv1    ),
    //     .in_edges   ( edges_to_u_conv1    ),
    //     .weights    ( weights_conv1       ),
    //     .bias       ( bias_conv1          ),
    //     .out_event  ( event_to_u_agg_max1 ),
    //     .out_edges  ( edges_to_u_agg_max1 ),
    //     .features   ( conv_features_to_u_agg_max1 )
    // );

    // MULTIPLE CONVOLUTIONS


    // average #(
    // ) u_average (
    //     .clk          ( clk                 ),
    //     .reset        ( reset               ),
    //     .is_valid     ( is_valid            ),
    //     .in_event     ( event_to_feature_mem4 ),
    //     .in_edges     ( edges_to_feature_mem4 ),
    //     .in_features  ( conv_features_to_u_agg_max4 ),
    //     .n            ( n           ),
    //     .out_feature  ( out_feature ),
    //     .out_valid    ( out_valid ),
    //     .empty        ( empty     )
    //  );
     
endmodule : top
