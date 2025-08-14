`timescale 1ns / 1ps

import graph_pkg::*;

module gru_head #(
    parameter int PRECISION            = 8,
    parameter int CLS_NUM              = 20,
    parameter int HEAD_DIM             = 72,
    parameter string INIT_PATH         = "/home/pwz/Repo/gcnn-audio-fpga/HW/mem/head.mem"
)(
    input logic clk,
    input logic reset,
    input logic [PRECISION-1 :0]   in_features [HEAD_DIM-1 : 0],
    input logic in_valid,

    output logic                   out_valid,
    output logic [PRECISION-1 :0]  out_conf,
    output logic [PRECISION-1 :0]  out_cls [CLS_NUM-1:0]
);

    logic [31:0]     multiplier [2:0] = {11527193, 18953250, 14189199};
    logic [PRECISION-1:0]  zp_w [2:0] = {119, 110, 157};
    logic [PRECISION-1:0]  zp_o [2:0] = {117, 136, 147};

    localparam ITERATIONS = HEAD_DIM/2;
    localparam IDLE = 3'd0;
    localparam LINEAR_1 = 3'd1;
    localparam LINEAR_2 = 3'd2;
    localparam GRU_X = 3'd3;
    localparam PREPARE_HEAD = 3'd4;
    localparam CLS_HEAD = 3'd5;
    localparam GRU_H = 3'd6;

    logic [2:0] state = IDLE;
    logic [2:0] state_reg = IDLE;
    logic [3:0] layer = 0;
    logic en;
    logic en_read_w;
    logic en_in_mul;
    logic [9:0] counter, counter_select, counter_mul_out;

    logic [PRECISION-1:0] features [HEAD_DIM-1:0];
    logic [PRECISION-1:0] i_r [HEAD_DIM-1:0];
    logic [PRECISION-1:0] i_z [HEAD_DIM-1:0];
    logic [PRECISION-1:0] i_n [HEAD_DIM-1:0];
    logic [PRECISION-1:0] h_r [HEAD_DIM-1:0];
    logic [PRECISION-1:0] h_z [HEAD_DIM-1:0];
    logic [PRECISION-1:0] h_n [HEAD_DIM-1:0];

    logic [PRECISION-1:0] output1;
    logic [PRECISION-1:0] output2;
    logic [PRECISION-1:0] output1_reg;
    logic [PRECISION-1:0] output2_reg;
    logic [PRECISION-1:0] output_linear [HEAD_DIM-1:0];
    logic delay_one = 0;
    logic is_relu = 0;
    logic is_relu_read_w = 0;
    logic is_relu_mul = 0;

    // Control state machine
    always @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
            counter <= '0;
            en <= '0;
            en_read_w <= '0;
            en_in_mul <= '0;
            layer <= '0;
            is_relu <= '1;
            is_relu_read_w <= '1;
            is_relu_mul <= 1;
            delay_one <= 0;
        end else begin
            case(state)
                IDLE: begin
                    if (in_valid) begin
                        state <= state+1;
                        counter <= '0;
                        en <= 1;
                        is_relu <= '1;
                        layer <= '0;
                        features <= in_features;
                    end
                end
                LINEAR_1: begin
                    if (counter < ITERATIONS-1) counter <= counter + 1;
                    if (counter == ITERATIONS-1) en <= 0;
                    if (counter_mul_out == ITERATIONS-1) delay_one <= 1;
                    if ((counter_mul_out == ITERATIONS-1) && delay_one) begin
                        delay_one <= 0;
                        counter <= HEAD_DIM;
                        state <= state+1;
                        en <= '1;
                        layer <= 1;
                        features <= output_linear;
                    end
                end
                LINEAR_2: begin
                    if (counter < (HEAD_DIM+ITERATIONS)-1) counter <= counter + 1;
                    if (counter == (HEAD_DIM+ITERATIONS)-1) en <= 0;
                    if (counter_mul_out == (HEAD_DIM+ITERATIONS)-1) delay_one <= 1;
                    if ((counter_mul_out == (HEAD_DIM+ITERATIONS)-1) && delay_one) begin
                        state <= state+1;
                        counter <= HEAD_DIM*2;
                        en <= '1;
                        layer <= 2;
                        delay_one <= 0;
                        is_relu <= 0;
                        features <= output_linear;
                    end
                end
                GRU_X: begin
                    if (counter < ((HEAD_DIM*4)+ITERATIONS)-1) counter <= counter + 1;
                    if (counter == ((HEAD_DIM*2)+ITERATIONS)-1) counter <= HEAD_DIM*3;
                    if (counter == ((HEAD_DIM*3)+ITERATIONS)-1) counter <= HEAD_DIM*4;                    
                    if (counter == ((HEAD_DIM*4)+ITERATIONS)-1) en <= 0;

                    if (counter_mul_out == HEAD_DIM*3) begin
                        i_r <= output_linear;
                    end
                    if (counter_mul_out == HEAD_DIM*4 ) begin
                        i_z <= output_linear;
                    end
                    if (counter_mul_out == ((HEAD_DIM*4)+ITERATIONS)-1) delay_one <= 1;
                    if (counter_mul_out == ((HEAD_DIM*4)+ITERATIONS)-1 && delay_one) begin
                        state <= state+1;
                        delay_one <= 0;
                        i_n <= output_linear;
                    end
                end
                // LINEAR_CLS: begin
                //     counter <= counter + 1;
                //     if (counter == CLS_NUM-1) begin
                //         state <= state+1;
                //         counter <= '0;
                //     end
                // end
                // LINEAR_CONF: begin
                //     state <= state+1;
                // end
                default: begin
                    counter <= counter + 1;
                    if (counter == ITERATIONS-1) begin
                        state <= state+1;
                        counter <= '0;
                    end
                end
            endcase
            en_read_w <= en;
            en_in_mul <= en_read_w;
            is_relu_read_w <= is_relu;
            is_relu_mul <= is_relu_read_w;
        end
    end

    assign counter_select = counter_mul_out % HEAD_DIM;

    /////////////////////////////////////////////////////////////////
    //                      Quantize inputs                        //
    /////////////////////////////////////////////////////////////////

    //Prepare weights
    localparam WEIGHT_DWIDTH = (HEAD_DIM*PRECISION)+32;
    localparam WEIGHT_AWIDTH = $clog2((HEAD_DIM*8)+CLS_NUM+1);
    logic [WEIGHT_DWIDTH-1 : 0] weight_mem1;
    logic [WEIGHT_DWIDTH-1 : 0] weight_mem2;
    logic [PRECISION-1:0]  single_weight1 [HEAD_DIM-1:0];
    logic [31:0]           single_bias1;
    logic [PRECISION-1:0]  single_weight2 [HEAD_DIM-1:0];
    logic [31:0]           single_bias2;

    delay_module #(
        .N        ( 10 ),
        .DELAY    ( 10 )
    ) delay_counter (
        .clk   ( clk             ),
        .idata ( counter         ),
        .odata ( counter_mul_out )
    );

    dual_port_memory_weights #(
        .AWIDTH   ( WEIGHT_AWIDTH  ),
        .DWIDTH   ( WEIGHT_DWIDTH  ),
        .STEP     ( 36             ),
        .RAM_TYPE ( "block"        ),
        .INIT_PATH ( INIT_PATH     )
    ) weights_memory   (
        .clk      ( clk             ),
        .en       ( state != IDLE   ),
        .addr     ( counter         ),
        .dout1    ( weight_mem1     ),
        .dout2    ( weight_mem2     )
    );

    genvar w;
    generate
        for (w = 0; w < HEAD_DIM; w++) begin : weights_assign
            always @(posedge clk) begin
                single_weight1[w] <= weight_mem1[(((PRECISION)*(w+1))-1)+32 : ((PRECISION)*w)+32];
                single_weight2[w] <= weight_mem2[(((PRECISION)*(w+1))-1)+32 : ((PRECISION)*w)+32];
            end
        end
    endgenerate

    always @(posedge clk) begin
        single_bias1 <= weight_mem1[31:0];
        single_bias2 <= weight_mem2[31:0];
    end

    //Handle multiplications and outputs
    vec_mul #(
        .INPUT_DIM         ( HEAD_DIM   ),
        .PRECISION_IN      ( PRECISION  ),
        .PRECISION_OUT     ( PRECISION  )
    ) mul_1 ( // Latency = 7
        .clk               ( clk               ),
        .en                ( en_in_mul         ),
        .feature_vector    ( features          ),
        .weight_vector     ( single_weight1    ),
        .bias              ( single_bias1      ),
        .relu              ( is_relu_mul       ),
        .multiplier        ( multiplier[layer] ),
        .zero_point_weight ( zp_w[layer]       ),
        .zero_point_out    ( zp_o[layer]       ),
        .result            ( output1           )
    );

    vec_mul #(
        .INPUT_DIM         ( HEAD_DIM   ),
        .PRECISION_IN      ( PRECISION  ),
        .PRECISION_OUT     ( PRECISION  )
    ) mul_2 (
        .clk               ( clk                  ),
        .en                ( en_in_mul            ),
        .feature_vector    ( features             ),
        .weight_vector     ( single_weight2       ),
        .bias              ( single_bias2         ),
        .relu              ( is_relu_mul          ),
        .multiplier        ( multiplier[layer]    ),
        .zero_point_weight ( zp_w[layer]          ),
        .zero_point_out    ( zp_o[layer]          ),
        .result            ( output2              )
    );


    always @(posedge clk) begin
        output1_reg <= output1;
        output2_reg <= output2;
        output_linear[counter_select] <= output1_reg;
        output_linear[counter_select+36] <= output2_reg;
        output_linear[counter_select] <= output1_reg;
        output_linear[counter_select+36] <= output2_reg;
    end

    // synthesis translate_off
    always @(posedge clk) begin
        if (state_reg != IDLE && in_valid) begin
            $display("GRU HEAD IS BROKEN - OVERFLOW!");
            $stop;
        end
    end
    // synthesis translate_on

endmodule