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
    
    logic [PRECISION-1 : 0] conv_features_to_u_agg_max1 [OUTPUT_DIM_1-1 : 0];
    logic [PRECISION-1 : 0] conv_features_to_u_agg_max2 [OUTPUT_DIM_2-1 : 0];
    logic [PRECISION-1 : 0] conv_features_to_u_agg_max3 [OUTPUT_DIM_3-1 : 0];
    logic [PRECISION-1 : 0] conv_features_to_u_agg_max4 [OUTPUT_DIM_4-1 : 0];
    
    logic [PRECISION-1 : 0] features_a_to_conv2 [OUTPUT_DIM_2-1:0];
    logic [PRECISION-1 : 0] features_a_to_conv3 [OUTPUT_DIM_3-1:0];
    logic [PRECISION-1 : 0] features_a_to_conv4 [OUTPUT_DIM_4-1:0];

    logic [PRECISION-1 : 0] features_b_to_conv2 [OUTPUT_DIM_2-1:0];   
    logic [PRECISION-1 : 0] features_b_to_conv3 [OUTPUT_DIM_3-1:0];   
    logic [PRECISION-1 : 0] features_b_to_conv4 [OUTPUT_DIM_4-1:0];   

    logic [PRECISION-1 : 0] feature_to_feature_mem1 [OUTPUT_DIM_1-1 : 0];
    logic [PRECISION-1 : 0] feature_to_feature_mem2 [OUTPUT_DIM_2-1 : 0];
    logic [PRECISION-1 : 0] feature_to_feature_mem3 [OUTPUT_DIM_3-1 : 0];
    logic [PRECISION-1 : 0] feature_to_feature_mem4 [OUTPUT_DIM_4-1 : 0];
    
    logic        [N_WIDTH-1 : 0] n;
    logic                        empty;
    
    logic signed [PRECISION : 0] weights_conv1 [OUTPUT_DIM_1-1:0][INPUT_DIM_1-1:0];
    initial begin
        weights_conv1[0]  = {1,0,0,0};
        weights_conv1[1]  = {0,1,0,0};
        weights_conv1[2]  = {0,-50,1,0};
        weights_conv1[3]  = {0,-50,0,1};
        weights_conv1[4]  = {0,-50,0,0};
        weights_conv1[5]  = {0,7,0,3};
        weights_conv1[6]  = {0,7,0,3};
        weights_conv1[7]  = {0,7,0,3};
        weights_conv1[8]  = {0,125,0,3};
        weights_conv1[9]  = {0,125,7,3};
        weights_conv1[10] = {0,125,7,3};
        weights_conv1[11] = {0,125,7,3};
        weights_conv1[12] = {2,125,7,3};
        weights_conv1[13] = {2,125,7,3};
        weights_conv1[14] = {2,125,7,3};
        weights_conv1[15] = {2,125,7,3};
        weights_conv1[16] = {2,125,7,3};
        weights_conv1[17] = {2,125,7,3};
        weights_conv1[18] = {2,125,7,3};
        weights_conv1[19] = {2,125,7,3};
        weights_conv1[20] = {2,125,7,3};
        weights_conv1[21] = {2,125,7,3};
        weights_conv1[22] = {2,125,7,3};
        weights_conv1[23] = {2,0,7,3};
        weights_conv1[24] = {2,0,7,3};
        weights_conv1[25] = {2,0,0,3};
        weights_conv1[26] = {2,0,-32,3};
        weights_conv1[27] = {2,0,-32,3};
        weights_conv1[28] = {2,0,-32,3};
        weights_conv1[29] = {2,0,-32,3};
        weights_conv1[30] = {0,0,-32,3};
        weights_conv1[31] = {2,0,-32,3};
        weights_conv1[32]  = {0,-50,1,0};
        weights_conv1[33]  = {0,-50,0,1};
        weights_conv1[34]  = {0,-50,0,0};
        weights_conv1[35]  = {0,7,0,3};
        weights_conv1[36]  = {0,7,0,3};
        weights_conv1[37]  = {0,7,0,3};
        weights_conv1[38]  = {0,125,0,3};
        weights_conv1[39]  = {0,125,7,3};
        weights_conv1[40] = {0,125,7,3};
        weights_conv1[41]  = {0,-50,1,0};
        weights_conv1[42]  = {0,-50,1,0};
        weights_conv1[43]  = {0,-50,0,1};
        weights_conv1[44]  = {0,-50,0,0};
        weights_conv1[45]  = {0,7,0,3};
        weights_conv1[46]  = {0,7,0,3};
        weights_conv1[47]  = {0,7,0,3};
        weights_conv1[48]  = {0,125,0,3};
        weights_conv1[49]  = {0,125,7,3};
        weights_conv1[50] = {0,125,7,3};
        weights_conv1[51]  = {0,-50,1,0};
        weights_conv1[52]  = {0,-50,1,0};
        weights_conv1[53]  = {0,-50,0,1};
        weights_conv1[54]  = {0,-50,0,0};
        weights_conv1[55]  = {0,7,0,3};
        weights_conv1[56]  = {0,7,0,3};
        weights_conv1[57]  = {0,7,0,3};
        weights_conv1[58]  = {0,125,0,3};
        weights_conv1[59]  = {0,125,7,3};
        weights_conv1[60] = {0,125,7,3};
        weights_conv1[61]  = {0,-50,1,0};
        weights_conv1[62]  = {0,-50,1,0};
        weights_conv1[63]  = {0,-50,0,1};
    end

    const logic signed [PRECISION: 0] bias_conv1 [OUTPUT_DIM_1-1:0] = {0,0,0,0,0,78,0,8,0,3,0,0,47,0,86,0,3,0,0,0,0,0,0,3,0,9,0,0,0,0,0,0,
                                                                       0,0,0,0,0,78,0,8,0,3,0,0,47,0,86,0,3,0,0,0,0,0,0,3,0,9,0,0,0,0,0,0};

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
