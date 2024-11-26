`timescale 1ns / 1ps

import graph_pkg::*;

module async_conv #(
    parameter int INPUT_DIM = INPUT_DIM_1,
    parameter int OUTPUT_DIM = OUTPUT_DIM_1
)( 
    input  logic                             clk,
    input  logic                             reset,
    input  event_type                        in_event,
    input  edge_type   [MAX_EDGES-1 : 0]     in_edges,

    input  logic signed [PRECISION : 0]    weights   [OUTPUT_DIM-1 : 0][INPUT_DIM-1 : 0],
    input  logic signed [PRECISION : 0]    bias      [OUTPUT_DIM-1 : 0],

    output event_type                        out_event,
    output edge_type    [MAX_EDGES-1 : 0]    out_edges,
    output logic [PRECISION-1 : 0]    features  [OUTPUT_DIM-1 : 0] //signed but only pos
);

//    event_type                             temp_event;
    edge_type   [MAX_EDGES-1 : 0]          temp_edges;

    logic [$clog2(MEMORY_OPS_NUM)-1 : 0]  counter;

    //SHOULD FIX HERE
    logic signed [PRECISION : 0]  feature_mat_a  [INPUT_DIM-1 : 0];
    logic signed [PRECISION : 0]  feature_mat_b  [INPUT_DIM-1 : 0];
    logic signed [PRECISION : 0]  output_mat_a   [OUTPUT_DIM-1 : 0];
    logic signed [PRECISION : 0]  output_mat_b   [OUTPUT_DIM-1 : 0];
                  
    logic [PRECISION-1 : 0]  features_a     [OUTPUT_DIM-1 : 0];
    logic [PRECISION-1 : 0]  features_b     [OUTPUT_DIM-1 : 0];

    // Counters control, input data assignments
    always @(posedge clk) begin
        if (reset) begin
            counter <= 0;
        end else begin
            if (in_event.valid) begin
                temp_edges <= in_edges;
                counter <= 0;
            end
            if (counter < MEMORY_OPS_NUM-1) begin
                counter <= counter + 1;
            end
        end
    end

    // feature_mat f, t, dt, dy
    // porta
    always @(posedge clk) begin
        feature_mat_a[0] <= ((counter == MEMORY_OPS_NUM-1) ? '0 : (temp_edges[counter].f ));
        feature_mat_a[1] <= ((counter == MEMORY_OPS_NUM-1) ? '0 : (temp_edges[counter].t )) >>> (T_WIDTH-PRECISION);
        feature_mat_a[2] <= ((counter == MEMORY_OPS_NUM-1) ? '0 : (temp_edges[counter].df));
        feature_mat_a[3] <= ((counter == MEMORY_OPS_NUM-1) ? '0 : (temp_edges[counter].dt)) >>> (T_WIDTH-PRECISION);
    end

    matrix_multiplication #(
        .INPUT_DIM (INPUT_DIM),
        .OUTPUT_DIM (OUTPUT_DIM)
    ) mul_a (
        .clk             ( clk             ),
        .reset           ( reset           ),
        .feature_matrix  ( feature_mat_a   ),
        .bias            ( bias            ),
        .weight_matrix   ( weights         ),
        .output_matrix   ( output_mat_a    )
    );

    // portb
    always @(posedge clk) begin
        feature_mat_b[0] <= ((counter == MEMORY_OPS_NUM-1) ? '0 : temp_edges[counter + MEMORY_OPS_NUM-1].f );
        feature_mat_b[1] <= ((counter == MEMORY_OPS_NUM-1) ? '0 : temp_edges[counter + MEMORY_OPS_NUM-1].t ) >>> (T_WIDTH-PRECISION);
        feature_mat_b[2] <= ((counter == MEMORY_OPS_NUM-1) ? '0 : temp_edges[counter + MEMORY_OPS_NUM-1].df);
        feature_mat_b[3] <= ((counter == MEMORY_OPS_NUM-1) ? '0 : temp_edges[counter + MEMORY_OPS_NUM-1].dt) >>> (T_WIDTH-PRECISION);
    end

    matrix_multiplication #(
        .INPUT_DIM (INPUT_DIM),
        .OUTPUT_DIM (OUTPUT_DIM)
    ) mul_b (
        .clk             ( clk             ),
        .reset           ( reset           ),
        .feature_matrix  ( feature_mat_b   ),
        .bias            ( bias            ),
        .weight_matrix   ( weights         ),
        .output_matrix   ( output_mat_b    )
    );
    
    logic [PRECISION-1:0] zero = '0;

    // RELU
    genvar i;
    generate
        for (i = 0; i < OUTPUT_DIM; i++) begin : rows
            always @(posedge clk) begin
                features_a[i] <= (ZERO_POINT > output_mat_a[i]) ? ZERO_POINT : $unsigned(output_mat_a[i]);
                features_b[i] <= (ZERO_POINT > output_mat_b[i]) ? ZERO_POINT : $unsigned(output_mat_b[i]);
            end
            
            always @(posedge clk) begin
                features[i] <= features_a[i] > features_b[i] ? features_a[i] : features_b[i];
            end
        end
    endgenerate

    // Output control, valid delay
    delay_module #(
        .N        ( F_WIDTH + T_WIDTH  + 1  ),
        .DELAY    ( 4 ) 
    ) delay_event (
        .clk   ( clk            ),
        .idata ( {in_event.t,  in_event.f, in_event.valid } ),
        .odata ( {out_event.t, out_event.f, out_event.valid} )
    );

    genvar j;
    generate
        for (j = 0; j < MAX_EDGES; j = j + 1) begin
            delay_module #(
                .N        ( F_WIDTH*2 + T_WIDTH*2  + 1  ),
                .DELAY    ( 4 ) // in_event -
            ) delay_edges (
                .clk   ( clk            ),
                .idata ( {in_edges[j].t,  in_edges[j].f,  in_edges[j].dt,  in_edges[j].df, in_edges[j].is_connected } ),
                .odata ( {out_edges[j].t, out_edges[j].f, out_edges[j].dt, out_edges[j].df, out_edges[j].is_connected} )
            );            
        end
    endgenerate 
endmodule
