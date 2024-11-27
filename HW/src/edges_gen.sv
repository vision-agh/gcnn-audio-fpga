`timescale 1ns / 1ps

import graph_pkg::*;

module edges_gen #(
    parameter int AWIDTH      = $clog2(NUM_CHANNEL), 
    parameter int DWIDTH      = T_WIDTH + 1,        
    parameter int FIFO_DEPTH  = 2**14,
    parameter int FIFO_WIDTH  = T_WIDTH + F_WIDTH + 1
)(
    input  logic                              clk,
    input  logic                              reset,
    input  logic signed     [T_WIDTH-1:0]     t,
    input  logic signed     [F_WIDTH-1:0]     f,
    input  logic                              is_valid,
    output graph_event_type                   out_event,
    output graph_edge_type  [MAX_EDGES-1:0]   out_edges,
    output logic            [N_WIDTH-1:0]     n,
    output logic                              empty,
    output logic            [T_WIDTH-1:0]     t_feature,
    output logic            [F_WIDTH-1:0]     f_feature
);

    // Internal signals for FIFO
    logic wen, fifo_read, full;
    logic [FIFO_WIDTH-1:0] din, dout;
    logic [$clog2(MEMORY_OPS_NUM)-1:0] counter, counter_reg;

    // FIFO instantiation
    fifo_wrapper_0 fifo_0 (
        .rst_0    ( reset     ),
        .wr_clk_0 ( clk       ),
        .wr_en    ( wen       ),
        .din      ( din       ),
        .full     ( full      ),
        .rd_en    ( fifo_read ),
        .dout     ( dout      ),
        .empty    ( empty     )
    );

    assign din = {t, f, is_valid};
    assign wen = is_valid;

    // FIFO event
    graph_event_type fifo_event, fifo_event_reg;

    always @(posedge clk) begin
        if (reset) begin
            n <= 0;
        end else if (is_valid) begin
            n <= n + 1;
        end
    end

    assign fifo_read = !empty && counter == MEMORY_OPS_NUM-1;

    // FIFO output parsing
    assign fifo_event.t     = dout[T_WIDTH+F_WIDTH:F_WIDTH+1];
    assign fifo_event.f     = dout[F_WIDTH:1];
    assign fifo_event.valid = dout[0];

    // Memory interface signals
    logic [AWIDTH-1:0] addra, addrb;
    logic [DWIDTH-1:0] dina, douta, doutb;
    logic ena, wea, web, enb;

    // Context memory instantiation
    memory #(
        .AWIDTH   ( AWIDTH  ),
        .DWIDTH   ( DWIDTH  ),
        .RAM_TYPE ( "block" )
    ) gen_memory (
        .clk      ( clk   ),
        .mem_ena  ( ena   ),
        .wea      ( wea   ),
        .addra    ( addra ),
        .dina     ( dina  ),
        .dinb     ( '0    ),
        .douta    ( douta ),
        .mem_enb  ( enb   ),
        .web      ( web   ),
        .addrb    ( addrb ),
        .doutb    ( doutb )
    );


    logic                           rd_a, rd_b, wr_a, rd_a_reg, rd_b_reg;
    logic                           condition_a, condition_b;
    logic           [AWIDTH-1:0]    f_coord_a, f_coord_b, f_coord_a_reg, f_coord_b_reg;
    graph_edge_type [MAX_EDGES-1:0] edges_reg;

    assign rd_a = ena & !wea;
    assign rd_b = enb & !wea;
    assign wr_a = ena & wea;

    assign ena  = (counter <= MEMORY_OPS_NUM-1 & condition_a) ? 1 : 0;
    assign enb  = (counter <= MEMORY_OPS_NUM-1 & condition_b) ? 1 : 0;
    assign wea  = (counter == 0) ? 1 : 0;
    assign dina = (counter == 0 & !empty) ? {fifo_event.t, 1'b1} : 0;
    assign web  = 1'b0;

    assign f_coord_a = fifo_event.f + counter*SKIP_STEP;
    assign f_coord_b = fifo_event.f - counter*SKIP_STEP;

    assign condition_a = (f_coord_a >= 0) && (f_coord_a < NUM_CHANNEL);
    assign condition_b = (f_coord_b >= 0) && (f_coord_b < NUM_CHANNEL);

    assign addra = f_coord_a;
    assign addrb = f_coord_b;
    
    logic [26-1 : 0] t_temp;
    logic [18-1 : 0] f_temp;
    logic [$clog2(MAX_EDGES)-1 : 0]             num_edges;
    
    logic port_a_valid,port_b_valid;
    assign port_a_valid = (rd_a_reg & douta[0]) && 
                          ((fifo_event_reg.t - douta[T_WIDTH:1]) < T_RADIUS) ? 1'b1 : 1'b0;
    assign port_b_valid = (rd_b_reg & doutb[0]) && 
                          ((fifo_event_reg.t - doutb[T_WIDTH:1]) < T_RADIUS) ? 1'b1 : 1'b0;
    
    // Counter and edge processing
    always @(posedge clk) begin
        if (reset) begin
            rd_a_reg <= 0;
            rd_b_reg <= 0;
            counter <= MEMORY_OPS_NUM-1;
        end else begin
            rd_a_reg <= rd_a;
            rd_b_reg <= rd_b;
            if (counter < MEMORY_OPS_NUM-1) begin
                counter <= counter + 1;
            end else begin
                counter <= 0;
            end
            if (counter_reg == MEMORY_OPS_NUM-1) begin
                t_temp <= '0;
                f_temp <= '0;
                num_edges <= '0;
            end else begin
                t_temp <= t_temp + (port_a_valid ? douta[T_WIDTH:1] : '0) + (port_b_valid ? doutb[T_WIDTH:1] : '0);
                f_temp <= f_temp + (port_a_valid ? f_coord_a_reg : '0) + (port_b_valid ? f_coord_b_reg : '0);
                num_edges <= num_edges + port_a_valid + port_b_valid;
            end
            
            // Port A
            edges_reg[counter_reg].t <= douta[T_WIDTH:1];
            edges_reg[counter_reg].f <= f_coord_a_reg;
            edges_reg[counter_reg].dt <= (rd_a_reg & douta[0]) ? fifo_event_reg.t - douta[T_WIDTH:1] : '0;
            edges_reg[counter_reg].df <= (rd_a_reg & douta[0]) ? fifo_event_reg.f - f_coord_a_reg : '0;
            edges_reg[counter_reg].is_connected <= port_a_valid;

            // Port B
            edges_reg[MEMORY_OPS_NUM-1+counter_reg].t <= doutb[T_WIDTH:1];
            edges_reg[MEMORY_OPS_NUM-1+counter_reg].f <= f_coord_b_reg;
            edges_reg[MEMORY_OPS_NUM-1+counter_reg].dt <= (rd_b_reg & doutb[0]) ? fifo_event_reg.t - doutb[T_WIDTH:1] : '0;
            edges_reg[MEMORY_OPS_NUM-1+counter_reg].df <= (rd_b_reg & doutb[0]) ? fifo_event_reg.f - f_coord_b_reg : '0;
            edges_reg[MEMORY_OPS_NUM-1+counter_reg].is_connected <= port_b_valid;
        end
    end
    
    logic  divisor_tvalid,dividend_tvalid,t_avg_valid,f_avg_valid;
    assign divisor_tvalid  = (counter_reg == MEMORY_OPS_NUM-1) && (num_edges != 0);
    assign dividend_tvalid = (counter_reg == MEMORY_OPS_NUM-1) && (num_edges != 0);
    
    logic [32-1 : 0] temp_t_feature;
    logic [24-1 : 0] temp_f_feature;
    assign t_feature = t_avg_valid ? temp_t_feature[22:2] : '0;
    assign f_feature = f_avg_valid ? {3'b0,temp_f_feature[19:2]} : '0;
    
    
    div_t div_t (
        .aclk                   ( clk             ),
        .s_axis_divisor_tdata   ( num_edges       ),
        .s_axis_divisor_tvalid  ( divisor_tvalid  ),
        .s_axis_dividend_tdata  ( t_temp          ),
        .s_axis_dividend_tvalid ( dividend_tvalid ),
        .m_axis_dout_tdata      ( temp_t_feature  ),//32
        .m_axis_dout_tvalid     ( t_avg_valid     )
    );
    
    div_f div_f (
        .aclk                   ( clk             ),
        .s_axis_divisor_tdata   ( num_edges       ),
        .s_axis_divisor_tvalid  ( divisor_tvalid  ),
        .s_axis_dividend_tdata  ( f_temp          ),
        .s_axis_dividend_tvalid ( dividend_tvalid ),
        .m_axis_dout_tdata      ( temp_f_feature  ),//32
        .m_axis_dout_tvalid     ( f_avg_valid     )
    );

    delay_module #(
        .N (AWIDTH*2),
        .DELAY (1)
    ) delay_f_coord (
        .clk ( clk ),
        .idata ( {f_coord_a,f_coord_b}         ),
        .odata ( {f_coord_a_reg,f_coord_b_reg} )
    );
    
    delay_module #(
        .N        ( F_WIDTH + T_WIDTH+1   ),
        .DELAY    ( 1 ) 
    ) delay_fifo_event (
        .clk   ( clk            ),
        .idata ( {fifo_event.t,     fifo_event.f,     fifo_event.valid}     ),
        .odata ( {fifo_event_reg.t, fifo_event_reg.f, fifo_event_reg.valid} )
    );
    
    delay_module #(
        .N        ( $clog2(MEMORY_OPS_NUM)   ),
        .DELAY    ( 2 ) 
    ) delay_counter (
        .clk   ( clk            ),
        .idata ( counter     ),
        .odata ( counter_reg )
    );
    
    delay_module #(
        .N (1),
        .DELAY (14)
    ) delay_fifo_read (
        .clk (clk),
        .idata ( fifo_read       ),
        .odata ( out_event.valid )
    );

    delay_module #(
        .N        ( F_WIDTH + T_WIDTH   ),
        .DELAY    ( 3 ) 
    ) delay_event (
        .clk   ( clk            ),
        .idata ( {fifo_event.t,  fifo_event.f} ),
        .odata ( {out_event.t,   out_event.f} )
    );

    // Output edges generation
    genvar i, j;
    generate
        for (i = 0; i < MEMORY_OPS_NUM-1; i++) begin
            always @(posedge clk) begin
                out_edges[i].t <= edges_reg[i].is_connected ? edges_reg[i].t : '0;
                out_edges[i].f <= edges_reg[i].is_connected ? edges_reg[i].f : '0;
                out_edges[i].dt <= edges_reg[i].is_connected ? edges_reg[i].dt : '0;
                out_edges[i].df <= edges_reg[i].is_connected ? edges_reg[i].df : '0;
                out_edges[i].is_connected <= edges_reg[i].is_connected;
            end
        end
        for (j = MEMORY_OPS_NUM-1; j < MAX_EDGES; j++) begin
            always @(posedge clk) begin
                out_edges[j].t <= edges_reg[j].is_connected ? edges_reg[j].t : '0;
                out_edges[j].f <= edges_reg[j].is_connected ? edges_reg[j].f : '0;
                out_edges[j].dt <= edges_reg[j].is_connected ? edges_reg[j].dt : '0;
                out_edges[j].df <= edges_reg[j].is_connected ? edges_reg[j].df : '0;
                out_edges[j].is_connected <= edges_reg[j].is_connected;
            end
        end
    endgenerate
endmodule

