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

    localparam string MEMORY_DIR_PATH = "/home/pwz/Repo/gcnn-audio-fpga/HW/mem/";
    localparam string INIT_PATH_CONV1 = {MEMORY_DIR_PATH, "conv_1_weights_small.mem"};
    localparam string INIT_PATH_CONV2 = {MEMORY_DIR_PATH, "conv_2_weights_small.mem"};
    localparam string INIT_PATH_CONV3 = {MEMORY_DIR_PATH, "conv_3_weights_small.mem"};
    localparam string INIT_PATH_CONV4 = {MEMORY_DIR_PATH, "conv_4_weights_small.mem"};

    parameter CONV1_MULTIPLIER_DIFF_T = 214742;
    parameter CONV1_MULTIPLIER_OUT = 59633;
    parameter CONV1_ZERO_POINT_IN = '0;
    parameter CONV1_ZERO_POINT_OUT = 31063;
    parameter CONV1_ZERO_POINT_WEIGHT = 28376;
    parameter logic [15:0] CONV1_SCALE_IN [21:0] = { 32767, 29490, 26214, 22937,
                                                     19660, 16383, 13107, 9830, 
                                                     6553,  3277,  0,     65534,
                                                     62257, 58981, 55704, 52427,
                                                     49150, 45874, 42597, 39320, 
                                                     36044, 32767 };

    parameter CONV2_MULTIPLIER_DIFF_T = 13843; //1384330
    parameter CONV2_MULTIPLIER_OUT = 225713;
    parameter CONV2_ZERO_POINT_IN = 31063;
    parameter CONV2_ZERO_POINT_OUT = 165;
    parameter CONV2_ZERO_POINT_WEIGHT = 137;
    parameter logic [15:0] CONV2_SCALE_IN [21:0] = { 2112, 1901, 1690, 1479,
                                                     1267, 1056, 845, 634,
                                                     422, 211, 0,  4225,
                                                     4013, 3802, 3591, 3380,
                                                     3168, 2957, 2746, 2535,
                                                     2324, 2112  };

    parameter CONV3_MULTIPLIER_DIFF_T = 44; //4417
    parameter CONV3_MULTIPLIER_OUT = 50218356;
    parameter CONV3_ZERO_POINT_IN = 165;
    parameter CONV3_ZERO_POINT_OUT = 135;
    parameter CONV3_ZERO_POINT_WEIGHT = 116;
    parameter logic [7:0] CONV3_SCALE_IN [21:0] = {7, 6, 5, 5, 4, 3, 3, 2, 1, 1, 0, 13, 13, 12, 11, 11, 10, 9, 9, 8, 7, 7};

    parameter CONV4_MULTIPLIER_DIFF_T = 57; //5690
    parameter CONV4_MULTIPLIER_OUT = 44180096;
    parameter CONV4_ZERO_POINT_IN = 135;
    parameter CONV4_ZERO_POINT_OUT = 133;
    parameter CONV4_ZERO_POINT_WEIGHT = 117;
    parameter logic [7:0] CONV4_SCALE_IN [21:0] = {9, 8, 7, 6, 5, 4, 3, 3, 2, 1, 0, 17, 16, 16, 15, 14, 13, 12, 11, 10, 10, 9};



    event_type                   event_to_conv1, event_to_conv2, event_to_conv3, event_to_conv4, event_to_avg;
    edge_type [MAX_EDGES-1:0]    edges_to_conv1, edges_to_conv2, edges_to_conv3, edges_to_conv4;
    logic [PRECISION_GEN-1:0]    f_feature;
    logic [PRECISION_GEN-1:0]    t_feature;
    logic [PRECISION_GEN-1:0]    features_to_conv1 [INPUT_DIM_1-1 : 0];
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
         .INIT_PATH         ( INIT_PATH_CONV1         )
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

     convolution_reversed #(
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
         .INIT_PATH         ( INIT_PATH_CONV2         ),
         .DSP               ( 1                       )
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

    convolution_reversed #(
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
        .INIT_PATH         ( INIT_PATH_CONV3         )
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

    convolution_reversed #(
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
        .INIT_PATH         ( INIT_PATH_CONV4         )
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
