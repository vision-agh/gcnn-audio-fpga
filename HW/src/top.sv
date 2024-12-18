`timescale 1ns / 1ps

import graph_pkg::*;

module top #(
)( 
    input logic                clk,
    input logic                reset,
    input logic [T_WIDTH-1: 0] t, 
    input logic [F_WIDTH-1: 0] f, 
    input logic                is_valid,
    input logic                is_last,

    output logic  [$clog2(OUTPUT_DIM_4)-1: 0] out_address, 
    output logic  [PRECISION_CONV4-1:0]       out_feature,
    output logic                              out_valid
);

    event_type                   event_to_conv1, event_to_conv2, event_to_conv3, event_to_conv4, event_to_avg;
    edge_type [MAX_EDGES-1:0]    edges_to_conv1, edges_to_conv2, edges_to_conv3, edges_to_conv4;
    logic [PRECISION_GEN-1:0]    f_feature;
    logic [PRECISION_GEN-1:0]    t_feature;
    logic [PRECISION_GEN-1 :0]   features_to_conv1 [INPUT_DIM_1-1 : 0];
    logic [PRECISION_CONV1-1 :0] features_to_conv2 [OUTPUT_DIM_1-1 : 0];
    logic [PRECISION_CONV2-1 :0] features_to_conv3 [OUTPUT_DIM_2-1 : 0];
    logic [PRECISION_CONV3-1 :0] features_to_conv4 [OUTPUT_DIM_3-1 : 0];
    logic [PRECISION_CONV4-1 :0] features_to_avg   [OUTPUT_DIM_4-1 : 0];

    generate_graph u_gen_graph (
        .clk        ( clk            ),
        .reset      ( reset          ),
        .t          ( t              ),
        .f          ( f              ),
        .is_valid   ( is_valid       ),
        .is_last    ( is_last        ),
        .out_event  ( event_to_conv1 ),
        .out_edges  ( edges_to_conv1 ),
        .t_feature  ( t_feature      ),
        .f_feature  ( f_feature      )
    );

    assign features_to_conv1[0] = f_feature;
    assign features_to_conv1[1] = t_feature;

     convolution #(
         .PRECISION_IN      ( PRECISION_GEN           ),
         .PRECISION_OUT     ( PRECISION_CONV1         ),
         .INPUT_DIM         ( INPUT_DIM_1             ),
         .OUTPUT_DIM        ( OUTPUT_DIM_1            ),
         .MULTIPLIER_DIFF_T ( CONV1_MULTIPLIER_DIFF_T ),
         .ZERO_POINT_IN     ( CONV1_ZERO_POINT_IN     ),
         .ZERO_POINT_OUT    ( CONV1_ZERO_POINT_OUT    ),
         .MULTIPLIER_OUT    ( CONV1_MULTIPLIER_OUT    ),
         .ZERO_POINT_WEIGHT ( CONV1_ZERO_POINT_WEIGHT ),
         .SCALE_IN          ( CONV1_SCALE_IN          ),          
         .INIT_PATH ( "/home/pwz/Repo/gcnn-audio-fpga/HW/mem/conv_1_weights.mem" )
     ) u_conv1 (
         .clk          ( clk               ),
         .reset        ( reset             ),
         .in_event     ( event_to_conv1    ),
         .in_edges     ( edges_to_conv1    ),
         .in_features  ( features_to_conv1 ),
         .out_event    ( event_to_conv2    ),
         .out_edges    ( edges_to_conv2    ),
         .out_features ( features_to_conv2 )
     );

     convolution #(
         .PRECISION_IN      ( PRECISION_CONV1         ),
         .PRECISION_OUT     ( PRECISION_CONV2         ),
         .INPUT_DIM         ( OUTPUT_DIM_1            ),
         .OUTPUT_DIM        ( OUTPUT_DIM_2            ),
         .MULTIPLIER_DIFF_T ( CONV2_MULTIPLIER_DIFF_T ),
         .ZERO_POINT_IN     ( CONV2_ZERO_POINT_IN     ),
         .ZERO_POINT_OUT    ( CONV2_ZERO_POINT_OUT    ),
         .MULTIPLIER_OUT    ( CONV2_MULTIPLIER_OUT    ),
         .ZERO_POINT_WEIGHT ( CONV2_ZERO_POINT_WEIGHT ),
         .SCALE_IN          ( CONV2_SCALE_IN          ),          
         .INIT_PATH ( "/home/pwz/Repo/gcnn-audio-fpga/HW/mem/conv_2_weights.mem" )
     ) u_conv2 (
         .clk          ( clk               ),
         .reset        ( reset             ),
         .in_event     ( event_to_conv2    ),
         .in_edges     ( edges_to_conv2    ),
         .in_features  ( features_to_conv2 ),
         .out_event    ( event_to_conv3    ),
         .out_edges    ( edges_to_conv3    ),
         .out_features ( features_to_conv3 )
     );

     convolution #(
         .PRECISION_IN      ( PRECISION_CONV2         ),
         .PRECISION_OUT     ( PRECISION_CONV3         ),
         .INPUT_DIM         ( OUTPUT_DIM_2            ),
         .OUTPUT_DIM        ( OUTPUT_DIM_3            ),
         .MULTIPLIER_DIFF_T ( CONV3_MULTIPLIER_DIFF_T ),
         .ZERO_POINT_IN     ( CONV3_ZERO_POINT_IN     ),
         .ZERO_POINT_OUT    ( CONV3_ZERO_POINT_OUT    ),
         .MULTIPLIER_OUT    ( CONV3_MULTIPLIER_OUT    ),
         .ZERO_POINT_WEIGHT ( CONV3_ZERO_POINT_WEIGHT ),
         .SCALE_IN          ( CONV3_SCALE_IN          ),          
         .INIT_PATH ( "/home/pwz/Repo/gcnn-audio-fpga/HW/mem/conv_3_weights.mem" )
     ) u_conv3 (
         .clk          ( clk               ),
         .reset        ( reset             ),
         .in_event     ( event_to_conv3    ),
         .in_edges     ( edges_to_conv3    ),
         .in_features  ( features_to_conv3 ),
         .out_event    ( event_to_conv4    ),
         .out_edges    ( edges_to_conv4    ),
         .out_features ( features_to_conv4 )
     );

     convolution #(
         .PRECISION_IN      ( PRECISION_CONV3         ),
         .PRECISION_OUT     ( PRECISION_CONV4         ),
         .INPUT_DIM         ( OUTPUT_DIM_3            ),
         .OUTPUT_DIM        ( OUTPUT_DIM_4            ),
         .MULTIPLIER_DIFF_T ( CONV4_MULTIPLIER_DIFF_T ),
         .ZERO_POINT_IN     ( CONV4_ZERO_POINT_IN     ),
         .ZERO_POINT_OUT    ( CONV4_ZERO_POINT_OUT    ),
         .MULTIPLIER_OUT    ( CONV4_MULTIPLIER_OUT    ),
         .ZERO_POINT_WEIGHT ( CONV4_ZERO_POINT_WEIGHT ),
         .SCALE_IN          ( CONV4_SCALE_IN          ),          
         .INIT_PATH ( "/home/pwz/Repo/gcnn-audio-fpga/HW/mem/conv_4_weights.mem" )
     ) u_conv4 (
         .clk          ( clk               ),
         .reset        ( reset             ),
         .in_event     ( event_to_conv4    ),
         .in_edges     ( edges_to_conv4    ),
         .in_features  ( features_to_conv4 ),
         .out_event    ( event_to_avg      ),
         .out_edges    (                   ),
         .out_features ( features_to_avg   )
     );

     average u_average (
         .clk                 ( clk                  ),
         .reset               ( reset                ),
         .in_event_valid      ( event_to_avg.valid   ),
         .in_features         ( features_to_avg      ),
         .data_input_finished ( event_to_avg.is_last ),
         .out_feature         ( out_feature          ),
         .out_valid           ( out_valid            ),
         .out_address         ( out_address          )
      );

endmodule : top
