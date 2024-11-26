`timescale 1ns / 1ps

import graph_pkg::*;

module matrix_multiplication #(
    parameter INPUT_DIM = INPUT_DIM_1,
    parameter OUTPUT_DIM = OUTPUT_DIM_1
)(
    input  logic                        clk,
    input  logic                        reset,
    input  logic signed [PRECISION :0]   feature_matrix [INPUT_DIM-1:0],
    input  logic signed [PRECISION :0]   weight_matrix  [OUTPUT_DIM-1:0][INPUT_DIM-1:0],
    input  logic signed [PRECISION :0]   bias           [OUTPUT_DIM-1:0],
    output logic signed [PRECISION :0]   output_matrix  [OUTPUT_DIM-1:0]
);

    logic signed [PRECISION*2 :0]  matrix_result [OUTPUT_DIM-1:0];

    genvar m;

    generate
        for (m = 0; m < OUTPUT_DIM; m++) begin : raw
            always @(posedge clk) begin
                matrix_result[m] = '0;
                for (int j = 0; j < INPUT_DIM; j = j + 1) begin : cols
                    matrix_result[m] = matrix_result[m] + (feature_matrix[j] * weight_matrix[m][j]);
                end
                output_matrix[m] <= (matrix_result[m] + bias[m]) >>> PRECISION;
            end
        end
    endgenerate

endmodule
