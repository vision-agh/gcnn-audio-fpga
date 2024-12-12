`timescale 1ns / 1ps

import graph_pkg::*;

module edges_gen #(
    parameter int AWIDTH      = $clog2(NUM_CHANNEL), 
    parameter int DWIDTH      = T_WIDTH + 1,          // t + valid
    parameter int FIFO_WIDTH  = T_WIDTH + F_WIDTH + 1 // t + f + valid
)(
    input logic clk,
    input logic reset,
    input event_type                          in_event,

    output event_type                         out_event,
    output edge_type  [MAX_EDGES-1:0]         out_edges
);
    
    logic [$clog2(F_RADIUS):0] counter, counter_reg;
    event_type in_event_reg; // fifo output

    localparam IDLE = 2'd0;
    localparam GGEN = 2'd1;
    logic state = IDLE;

    // Memory interface signals
    logic [AWIDTH-1:0] addra, addrb;
    logic [DWIDTH-1:0] dinb, douta, doutb;
    logic ena, wea, web, enb;

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
    edge_type [MAX_EDGES-1:0] edges_reg;

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

    logic [26-1 : 0] t_temp;
    logic start;
    logic [18-1 : 0] f_temp;
    logic [$clog2(MAX_EDGES)-1 : 0]             num_edges;

    // Counter and edge processing
    always @(posedge clk) begin
        if (reset) begin
            rd_a_reg <= 0;
            state <= IDLE;
            rd_b_reg <= 0;
            start <= '0;
            out_event.valid <= '0;
            counter <= F_RADIUS;
        end else begin
            if (counter < F_RADIUS && state==GGEN) begin
                counter <= counter + 1;
            end
            if (in_event.valid) begin
                counter <= '0;
                state <= GGEN;
                in_event_reg <= in_event;
            end
            if (counter_reg == F_RADIUS && counter == F_RADIUS && state == GGEN) begin
                state <= IDLE;
                start <= '1;
            end
            if (state == IDLE) begin
                if (start == 1) begin
                    out_edges <= edges_reg;
                    out_event <= in_event_reg;
                    start <= '0;
                end
                else begin
                    out_event.valid <= '0;
                end
            end
            counter_reg <= counter;
            condition_a_reg <= condition_a;
            condition_b_reg <= condition_b;
            
            // Port A
            edges_reg[counter_reg].dt            <= in_event_reg.t - douta[DWIDTH-1:1];
            edges_reg[counter_reg].is_connected  <= douta[0] && condition_a_reg && ((in_event_reg.t - douta[DWIDTH-1:1]) < T_RADIUS);
    
            // Port B (ON counter F_RADIUS we do write on B)
            if (counter_reg != F_RADIUS) begin
                edges_reg[F_RADIUS+1+counter_reg].dt            <= in_event_reg.t - doutb[DWIDTH-1:1];
                edges_reg[F_RADIUS+1+counter_reg].is_connected  <= doutb[0] && condition_b_reg && ((in_event_reg.t - doutb[DWIDTH-1:1]) < T_RADIUS);
            end
        end
    end
    
//    logic  divisor_tvalid,dividend_tvalid,t_avg_valid,f_avg_valid;
//    assign divisor_tvalid  = (counter_reg == MEMORY_OPS_NUM-1) && (num_edges != 0);
//    assign dividend_tvalid = (counter_reg == MEMORY_OPS_NUM-1) && (num_edges != 0);
    
//    logic [32-1 : 0] temp_t_feature;
//    logic [24-1 : 0] temp_f_feature;
//    assign t_feature = t_avg_valid ? temp_t_feature[22:2] : '0;
//    assign f_feature = f_avg_valid ? {3'b0,temp_f_feature[19:2]} : '0;
    
    
//    div_t div_t (
//        .aclk                   ( clk             ),
//        .s_axis_divisor_tdata   ( num_edges       ),//5bit
//        .s_axis_divisor_tvalid  ( divisor_tvalid  ),
//        .s_axis_dividend_tdata  ( t_temp          ),
//        .s_axis_dividend_tvalid ( dividend_tvalid ),//26bit
//        .m_axis_dout_tdata      ( temp_t_feature  ),
//        .m_axis_dout_tvalid     ( t_avg_valid     )
//    );
    
//    div_f div_f (
//        .aclk                   ( clk             ),
//        .s_axis_divisor_tdata   ( num_edges       ),//5bit
//        .s_axis_divisor_tvalid  ( divisor_tvalid  ),
//        .s_axis_dividend_tdata  ( f_temp          ),//18bit
//        .s_axis_dividend_tvalid ( dividend_tvalid ),
//        .m_axis_dout_tdata      ( temp_f_feature  ),
//        .m_axis_dout_tvalid     ( f_avg_valid     )
//    );

//    delay_module #(
//        .N     ( AWIDTH*2 ),
//        .DELAY ( 1        )
//    ) delay_f_coord (
//        .clk   ( clk                           ),
//        .idata ( {f_coord_a,    f_coord_b    } ),
//        .odata ( {f_coord_a_reg,f_coord_b_reg} )
//    );

//    // Output edges generation
//    genvar i, j;
//    generate
//        for (i = 0; i < MEMORY_OPS_NUM-1; i++) begin
//            always @(posedge clk) begin
//                out_edges[i].t            <= edges_reg[i].is_connected ? edges_reg[i].t : '0;
//                out_edges[i].f            <= edges_reg[i].is_connected ? edges_reg[i].f : '0;
//                out_edges[i].dt           <= edges_reg[i].is_connected ? edges_reg[i].dt : '0;
//                out_edges[i].df           <= edges_reg[i].is_connected ? edges_reg[i].df : '0;
//                out_edges[i].is_connected <= edges_reg[i].is_connected;
//            end
//        end
//        for (j = MEMORY_OPS_NUM-1; j < MAX_EDGES; j++) begin
//            always @(posedge clk) begin
//                out_edges[j].t            <= edges_reg[j].is_connected ? edges_reg[j].t : '0;
//                out_edges[j].f            <= edges_reg[j].is_connected ? edges_reg[j].f : '0;
//                out_edges[j].dt           <= edges_reg[j].is_connected ? edges_reg[j].dt : '0;
//                out_edges[j].df           <= edges_reg[j].is_connected ? edges_reg[j].df : '0;
//                out_edges[j].is_connected <= edges_reg[j].is_connected;
//            end
//        end
//    endgenerate

    // synthesis translate_off
    always @(posedge clk) begin
        if (state != IDLE && in_event.valid) begin
            $display("DECREASE THE FIFO THROUGHPUT");
            $stop;
        end
    end
    // synthesis translate_on

endmodule

