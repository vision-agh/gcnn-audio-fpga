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
    end

    //temporaly waight
    logic signed [PRECISION:0] weights_conv2 [OUTPUT_DIM_2-1:0][INPUT_DIM_2-1:0];
    initial begin
        weights_conv2[0] = {1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5};
        weights_conv2[1] = {1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5};
        weights_conv2[2] = {1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5};
        weights_conv2[3] = {1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5};
        weights_conv2[4] = {1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5};
        weights_conv2[5] = {1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5};
        weights_conv2[6] = {1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5};
        weights_conv2[7] = {1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5};
        weights_conv2[8] = {1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5};
        weights_conv2[9] = {1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5};
        weights_conv2[10] = {1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5};
        weights_conv2[11] = {1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5};
        weights_conv2[12] = {1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5};
        weights_conv2[13] = {1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5};
        weights_conv2[14] = {1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5,1,4,1,5};
        weights_conv2[15] = {1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1};
        weights_conv2[16] = {1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1};
        weights_conv2[17] = {8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1};
        weights_conv2[18] = {8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1};
        weights_conv2[19] = {8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1};
        weights_conv2[20] = {8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1};
        weights_conv2[21] = {8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1};
        weights_conv2[22] = {8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1};
        weights_conv2[23] = {8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1};
        weights_conv2[24] = {8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1};
        weights_conv2[25] = {8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1};
        weights_conv2[26] = {8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1};
        weights_conv2[27] = {8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1,1,4,8,1};
        weights_conv2[28] = {1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1};
        weights_conv2[29] = {1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1};
        weights_conv2[30] = {1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1,1,4,1,1};
        weights_conv2[31] = {1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4};
    end

    const logic signed [PRECISION: 0] bias_conv1 [OUTPUT_DIM_1-1:0] = {0,0,0,0,0,78,0,8,0,3,0,0,47,0,86,0,3,0,0,0,0,0,0,3,0,9,0,0,0,0,0,0};
    const logic signed [PRECISION: 0] bias_conv2 [OUTPUT_DIM_1-1:0] = {0,0,0,0,0,78,0,8,0,3,0,0,47,0,86,0,3,0,0,0,0,0,0,3,0,9,0,0,0,0,0,0};

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
    
    async_conv #(
        .INPUT_DIM  ( INPUT_DIM_1      ),
        .OUTPUT_DIM ( OUTPUT_DIM_1     )
    ) u_conv1 (
        .clk        ( clk              ),
        .reset      ( reset            ),
        .in_event   ( event_to_u_conv1 ),
        .in_edges   ( edges_to_u_conv1 ),
        .weights    ( weights_conv1    ),
        .bias       ( bias_conv1       ),
        .out_event  ( event_to_u_agg_max1 ),
        .out_edges  ( edges_to_u_agg_max1 ),
        .features   ( conv_features_to_u_agg_max1 )
    );
    
    agg_max #(
    ) u_agg_max1 (
        .clk          ( clk                   ),
        .reset        ( reset                 ),
        .in_event     ( event_to_u_agg_max1   ),
        .in_edges     ( edges_to_u_agg_max1   ),
        .in_features  ( conv_features_to_u_agg_max1 ),
        .out_feature  ( feature_to_feature_mem1 ),
        .out_event    ( event_to_feature_mem1 ),
        .out_edges    ( edges_to_feature_mem1 )
    );
    
    feature_memory #(
        .DWIDTH       ( OUTPUT_DIM_1 * PRECISION )
    ) u_feature_mem1 (
        .clk          ( clk                   ),
        .reset        ( reset                 ),
        .in_event     ( event_to_feature_mem1 ),
        .in_edges     ( edges_to_feature_mem1 ),
        .in_feature   ( feature_to_feature_mem1 ),
        .out_event    ( event_to_u_conv2        ),
        .out_edges    ( edges_to_u_conv2        ),
        .out_features_a ( features_a_to_conv2 ),
        .out_features_b ( features_b_to_conv2 )
    );
    
    sync_conv #(
        .INPUT_DIM    ( INPUT_DIM_2 ),
        .OUTPUT_DIM   ( OUTPUT_DIM_2 )
    ) u_conv2 (
        .clk          ( clk               ),
        .reset        ( reset             ),
        .in_event     ( event_to_u_conv2    ),
        .in_edges     ( edges_to_u_conv2    ),
        .weights      ( weights_conv2     ),
        .bias         ( bias_conv2        ),
        .in_features_a ( features_a_to_conv2 ),
        .in_features_b ( features_b_to_conv2 ),
        .out_event    ( event_to_u_agg_max2 ),
        .out_edges    ( edges_to_u_agg_max2 ),
        .features     ( conv_features_to_u_agg_max2 )
    );
    
    agg_max #(
    ) u_agg_max2 (
        .clk          ( clk                 ),
        .reset        ( reset               ),
        .in_event     ( event_to_u_agg_max2 ),
        .in_edges     ( edges_to_u_agg_max2 ),
        .in_features  ( conv_features_to_u_agg_max2 ),
        .out_feature  ( feature_to_feature_mem2 ),
        .out_event    ( event_to_feature_mem2 ),
        .out_edges    ( edges_to_feature_mem2 )
    );
    
    feature_memory #(
        .DWIDTH       ( OUTPUT_DIM_2 * PRECISION )
    ) u_feature_mem2 (
        .clk          ( clk                   ),
        .reset        ( reset                 ),
        .in_event     ( event_to_feature_mem2 ),
        .in_edges     ( edges_to_feature_mem2 ),
        .in_feature   ( feature_to_feature_mem2 ),
        .out_event    ( event_to_u_conv3        ),
        .out_edges    ( edges_to_u_conv3        ),
        .out_features_a ( features_a_to_conv3 ),
        .out_features_b ( features_b_to_conv3 )
    );
    
    sync_conv #(
        .INPUT_DIM    ( INPUT_DIM_3 ),
        .OUTPUT_DIM   ( OUTPUT_DIM_3 )
    ) u_conv3 (
        .clk          ( clk               ),
        .reset        ( reset             ),
        .in_event     ( event_to_u_conv3    ),
        .in_edges     ( edges_to_u_conv3    ),
        .weights      ( weights_conv2     ),
        .bias         ( bias_conv2        ),
        .in_features_a ( features_a_to_conv3 ),
        .in_features_b ( features_b_to_conv3 ),
        .out_event    ( event_to_u_agg_max3 ),
        .out_edges    ( edges_to_u_agg_max3 ),
        .features     ( conv_features_to_u_agg_max3 )
    );
    
    agg_max #(
    ) u_agg_max3 (
        .clk          ( clk                 ),
        .reset        ( reset               ),
        .in_event     ( event_to_u_agg_max3 ),
        .in_edges     ( edges_to_u_agg_max3 ),
        .in_features  ( conv_features_to_u_agg_max3 ),
        .out_feature  ( feature_to_feature_mem3 ),
        .out_event    ( event_to_feature_mem3 ),
        .out_edges    ( edges_to_feature_mem3 )
    );
    
    feature_memory #(
        .DWIDTH       ( OUTPUT_DIM_3 * PRECISION )
    ) u_feature_mem3 (
        .clk          ( clk                   ),
        .reset        ( reset                 ),
        .in_event     ( event_to_feature_mem3 ),
        .in_edges     ( edges_to_feature_mem3 ),
        .in_feature   ( feature_to_feature_mem3 ),
        .out_event    ( event_to_u_conv4        ),
        .out_edges    ( edges_to_u_conv4        ),
        .out_features_a ( features_a_to_conv4 ),
        .out_features_b ( features_b_to_conv4 )
    );
    
    sync_conv #(
        .INPUT_DIM    ( INPUT_DIM_4 ),
        .OUTPUT_DIM   ( OUTPUT_DIM_4 )
    ) u_conv4 (
        .clk          ( clk               ),
        .reset        ( reset             ),
        .in_event     ( event_to_u_conv4    ),
        .in_edges     ( edges_to_u_conv4    ),
        .weights      ( weights_conv2     ),
        .bias         ( bias_conv2        ),
        .in_features_a ( features_a_to_conv4 ),
        .in_features_b ( features_b_to_conv4 ),
        .out_event    ( event_to_u_agg_max4 ),
        .out_edges    ( edges_to_u_agg_max4 ),
        .features     ( conv_features_to_u_agg_max4 )
    );
    
    agg_max #(
    ) u_agg_max4 (
        .clk          ( clk                 ),
        .reset        ( reset               ),
        .in_event     ( event_to_u_agg_max4 ),
        .in_edges     ( edges_to_u_agg_max4 ),
        .in_features  ( conv_features_to_u_agg_max4 ),
        .out_feature  ( feature_to_feature_mem4 ),
        .out_event    ( event_to_feature_mem4 ),
        .out_edges    ( edges_to_feature_mem4 )
    );
    
    average #(
    ) u_average (
        .clk          ( clk                 ),
        .reset        ( reset               ),
        .is_valid     ( is_valid            ),
        .in_event     ( event_to_feature_mem4 ),
        .in_edges     ( edges_to_feature_mem4 ),
        .in_features  ( conv_features_to_u_agg_max4 ),
        .n            ( n           ),
        .out_feature  ( out_feature ),
        .out_valid    ( out_valid ),
        .empty        ( empty     )
     );
     
endmodule : top
