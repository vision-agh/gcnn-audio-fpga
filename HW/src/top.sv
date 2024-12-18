`timescale 1ns / 1ps

import graph_pkg::*;

module top #(
)( 
    input logic                           clk,
    input logic                           reset,
    input logic   [T_WIDTH-1: 0]          t, 
    input logic   [F_WIDTH-1: 0]          f, 
    input logic                           is_valid,

    output event_type                     out_event,
    output edge_type  [MAX_EDGES-1 : 0]   out_edges,

    output logic [PRECISION_CONV1-1 :0]   out_features [OUTPUT_DIM_1-1 : 0]

);

    event_type                event_to_u_agg_max1, event_to_u_agg_max2, event_to_u_agg_max3, event_to_u_agg_max4;
    edge_type [MAX_EDGES-1:0] edges_to_u_agg_max1, edges_to_u_agg_max2, edges_to_u_agg_max3, edges_to_u_agg_max4;
    
    event_type                event_to_feature_mem1, event_to_feature_mem2, event_to_feature_mem3, event_to_feature_mem4;
    edge_type [MAX_EDGES-1:0] edges_to_feature_mem1, edges_to_feature_mem2, edges_to_feature_mem3, edges_to_feature_mem4;
    
    event_type                event_to_u_conv1, event_to_u_conv2, event_to_u_conv3, event_to_u_conv4;
    edge_type [MAX_EDGES-1:0] edges_to_u_conv1, edges_to_u_conv2, edges_to_u_conv3, edges_to_u_conv4;

    logic    [PRECISION_GEN-1:0]   f_feature;
    logic    [PRECISION_GEN-1:0]   t_feature;

    logic [PRECISION_CONV1-1 :0]     features_to_conv1 [INPUT_DIM_1-1 : 0];

    generate_graph u_gen_graph (
        .clk        ( clk       ),
        .reset      ( reset     ),
        .t          ( t         ),
        .f          ( f         ),
        .is_valid   ( is_valid  ),
        .out_event  ( event_to_u_conv1 ),
        .out_edges  ( edges_to_u_conv1 ),
        .t_feature  ( t_feature ),
        .f_feature  ( f_feature )
    );

    assign features_to_conv1[0] = f_feature;
    assign features_to_conv1[1] = t_feature;
    
     convolution #(
         .INPUT_DIM  ( INPUT_DIM_1                                                ),
         .OUTPUT_DIM ( OUTPUT_DIM_1                                               ),
         .INIT_PATH  ( "/home/pwz/Repo/gcnn-audio-fpga/HW/mem/conv_1_weights.mem" )
     ) u_conv1 (
         .clk          ( clk                 ),
         .reset        ( reset               ),
         .in_event     ( event_to_u_conv1    ),
         .in_edges     ( edges_to_u_conv1    ),
         .in_features  ( features_to_conv1   ),
         .out_event    ( out_event           ),
         .out_edges    ( out_edges           ),
         .out_features ( out_features        )
     );

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

