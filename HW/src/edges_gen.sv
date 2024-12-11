`timescale 1ns / 1ps

import graph_pkg::*;

module edges_gen #(
    parameter int AWIDTH      = $clog2(NUM_CHANNEL), 
    parameter int DWIDTH      = T_WIDTH + 1,          // t + valid
    parameter int FIFO_WIDTH  = T_WIDTH + F_WIDTH + 1 // t + f + valid
)(
    input  logic                                          clk,
    input  logic                                          reset,
    input  event_type                                     in_event,

    output event_type                                     out_event,
    output edge_type_before_quantize  [MAX_EDGES-1:0]     out_edges,
    output logic                      [PRECISION_GEN-1:0] t_feature,
    output logic                      [PRECISION_GEN-1:0] f_feature
);
    
    logic [$clog2(F_RADIUS):0] counter, counter_reg;
    event_type in_event_reg, in_event_reg_2;

    localparam IDLE = 2'd0;
    localparam GGEN = 2'd1;
    logic state = IDLE;

    // Memory interface signals
    logic [AWIDTH-1:0] addra, addrb, addra_reg, addrb_reg;
    logic [DWIDTH-1:0] dinb, douta, doutb;
    logic ena, wea, web, enb;
    
    logic port_a_valid, port_b_valid;

    // Context memory instantiation
    memory #(
        .AWIDTH   ( AWIDTH  ),
        .DWIDTH   ( DWIDTH  ),
        .RAM_TYPE ( "block" )
    ) gen_memory (
        .clk      ( clk   ),
        .mem_ena  ( ena   ),    // READ only on PORTA
        .wea      ( wea   ),
        .addra    ( addra ),
        .dina     ( '0    ),
        .dinb     ( dinb  ),
        .douta    ( douta ),
        .mem_enb  ( enb   ),    // Write on last 
        .web      ( web   ),
        .addrb    ( addrb ),
        .doutb    ( doutb )
    );
    logic                           rd_a, rd_b, wr_a, rd_a_reg, rd_b_reg;
    logic                           condition_a, condition_b, condition_a_reg, condition_b_reg;
    edge_type_before_quantize [MAX_EDGES-1:0] edges_reg, edges_reg_2;

    assign rd_a = ena & !wea;
    assign rd_b = enb & !wea;
    assign wr_a = ena & wea;

    assign ena  = (counter <= F_RADIUS && condition_a && state==GGEN) ? 1'b1 : 1'b0;
    assign enb  = (counter <= F_RADIUS && condition_b && state==GGEN) ? 1'b1 : 1'b0;
    assign wea  = 0;
    assign dinb[DWIDTH-1 : 1] = in_event_reg.t;
    assign dinb[DWIDTH-1 : 0] = 1'b1;
    assign web  = (counter == F_RADIUS) && state==GGEN;

    assign addra = in_event.f + counter*SKIP_STEP;
    assign addrb = in_event.f - 100 + (counter*SKIP_STEP);

    assign condition_a = (addra >= 0) && (addra < NUM_CHANNEL);
    assign condition_b = (addrb >= 0) && (addrb < NUM_CHANNEL);

    logic [24-1 : 0] t_temp;
    logic start;
    logic [14-1 : 0] f_temp;
    logic [$clog2(MAX_EDGES)-1 : 0]             num_edges;

    // Counter and edge processing
    always @(posedge clk) begin
        if (reset) begin
            rd_a_reg <= 0;
            state <= IDLE;
            rd_b_reg <= 0;
            start <= '0;
//            out_event.valid <= '0;
            counter <= F_RADIUS;
            t_temp <= 0;
            num_edges <= 0;
            addra_reg <= '0;
            addrb_reg <= '0;
        end else begin
            if (counter < F_RADIUS && state==GGEN) begin
                counter <= counter + 1;
            end
            if (in_event.valid) begin
                counter <= '0;
                state <= GGEN;
                in_event_reg <= in_event;
                t_temp <= '0;
                f_temp <= '0;
                num_edges <= '0;
            end else begin
                t_temp  <= (port_a_valid ? douta[DWIDTH-1:1] : '0) + (port_b_valid ? doutb[DWIDTH-1:1] : '0) + t_temp;
                f_temp  <= (port_a_valid ? addra_reg : '0) + (port_b_valid ? addrb_reg : '0) + f_temp; 
                num_edges <= port_a_valid + port_b_valid + num_edges;
            end
            if (counter_reg == F_RADIUS && counter == F_RADIUS && state == GGEN) begin
                state <= IDLE;
                start <= '1;
            end
            if (state == IDLE) begin
                if (start == 1) begin
                    edges_reg_2 <= edges_reg;
                    in_event_reg_2 <= in_event_reg;
                    start <= '0;
                end
//                else begin
//                    out_event.valid <= '0;
//                end
            end
            counter_reg <= counter;
            condition_a_reg <= condition_a;
            condition_b_reg <= condition_b;
            
            // Port A
            edges_reg[counter_reg].dt            <= in_event_reg.t - douta[DWIDTH-1:1];
            edges_reg[counter_reg].is_connected  <= port_a_valid;
    
            // Port B (ON counter F_RADIUS we do write on B)
            if (counter_reg != F_RADIUS) begin
                edges_reg[F_RADIUS+1+counter_reg].dt            <= in_event_reg.t - doutb[DWIDTH-1:1];
                edges_reg[F_RADIUS+1+counter_reg].is_connected  <= port_b_valid;
            end
            
            addra_reg <= addra;
            addrb_reg <= addrb;
            
        end
    end
    
    assign port_a_valid = douta[0] && condition_a_reg && ((in_event_reg.t - douta[DWIDTH-1:1]) < T_RADIUS);
    assign port_b_valid = doutb[0] && condition_b_reg && ((in_event_reg.t - doutb[DWIDTH-1:1]) < T_RADIUS) && (counter_reg != F_RADIUS);
   
    logic  divisor_tvalid,dividend_tvalid,t_avg_valid,f_avg_valid;
    
    always @(posedge clk) begin
        if(reset) begin
            divisor_tvalid <= 0;
            dividend_tvalid <= 0;
        end else begin
            if((counter_reg == F_RADIUS) && (num_edges != 0)) begin
                divisor_tvalid <= 1;
                dividend_tvalid <= 1;
            end else begin
                divisor_tvalid <= 0;
                dividend_tvalid <= 0;
            end
        end
    end

    
    logic [40-1 : 0] t_average;
    logic [30-1 : 0] f_average;
    logic [40+$clog2(T_MULTIPLIER)-1:0] extended_t_average,temp_t_average;
    logic [30+$clog2(F_MULTIPLIER)-1:0] extended_f_average,temp_f_average;
    
    assign extended_t_average = t_avg_valid ? {{ $clog2(T_MULTIPLIER){1'b0} }, t_average} : '0;
    assign extended_f_average = f_avg_valid ? {{ $clog2(F_MULTIPLIER){1'b0} }, f_average} : '0;
    
    assign temp_t_average = (extended_t_average * T_MULTIPLIER >>> 16) + ZERO_POINT;
    assign temp_f_average = (extended_f_average * F_MULTIPLIER >>> 16) + ZERO_POINT;
    //rounding
    assign t_feature = temp_t_average[PRECISION_GEN-1] ? temp_t_average[16+:PRECISION_GEN] + 1 : temp_t_average[16+:PRECISION_GEN];
    assign f_feature = temp_f_average[PRECISION_GEN-1] ? temp_f_average[16+:PRECISION_GEN] + 1 : temp_f_average[16+:PRECISION_GEN];
    
    div_t div_t ( //32 clock latency
        .aclk                   ( clk             ),
        .s_axis_divisor_tdata   ( num_edges       ),//5bit
        .s_axis_divisor_tvalid  ( divisor_tvalid  ),
        .s_axis_dividend_tdata  ( t_temp          ),//24bit
        .s_axis_dividend_tvalid ( dividend_tvalid ),
        .m_axis_dout_tdata      ( t_average       ),//39 ~16 15~0
        .m_axis_dout_tvalid     ( t_avg_valid     )
    );
    
    div_f div_f (//32 clock latency
        .aclk                   ( clk             ),
        .s_axis_divisor_tdata   ( num_edges       ),//5bit
        .s_axis_divisor_tvalid  ( divisor_tvalid  ),
        .s_axis_dividend_tdata  ( f_temp          ),//14bit
        .s_axis_dividend_tvalid ( dividend_tvalid ),
        .m_axis_dout_tdata      ( f_average       ),//30~16 15~0
        .m_axis_dout_tvalid     ( f_avg_valid     )
    );
    
    // wait for the result of divider
    delay_module #(
        .N        ( F_WIDTH + T_WIDTH  + 1),
        .DELAY    ( 31 )
    ) delay_event (
        .clk   (clk),
        .idata ({in_event_reg_2.t,  in_event_reg_2.f, in_event_reg_2.valid}),
        .odata ({out_event.t, out_event.f, out_event.valid})
    );

    genvar j;
    generate
        for (j = 0; j < MAX_EDGES; j = j + 1) begin
            delay_module #(
                .N        ( T_WIDTH + 1),
                .DELAY    ( 31 )
            ) delay_edges (
                .clk   (clk),
                .idata ({edges_reg_2[j].dt,edges_reg_2[j].is_connected}),
                .odata ({out_edges[j].dt,out_edges[j].is_connected})
            );            
        end
    endgenerate  

    // synthesis translate_off
    always @(posedge clk) begin
        if (state != IDLE && in_event.valid) begin
            $display("DECREASE THE FIFO THROUGHPUT");
            $stop;
        end
    end
    // synthesis translate_on

endmodule

