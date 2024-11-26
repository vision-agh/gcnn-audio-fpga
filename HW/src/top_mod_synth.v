module top_mod_synth ( 
    input   clk,
    input   reset,
    input   [9:0]frequency,
    input   [20:0]timestamp,
    input   in_valid,
    input   data_input_finished,
    output  [4:0]address,
    output  [7:0]feature,
    output  out_valid
);

    top #(
    ) u_top (
        .clk                 ( clk                 ),
        .reset               ( reset               ),
        .t                   ( timestamp           ),
        .f                   ( {11'b0,f}           ),
        .is_valid            ( in_valid            ),
        .data_input_finished ( data_input_finished ),
        .out_address         ( address             ),
        .out_feature         ( feature             ),
        .out_valid           ( out_valid           )
    );

endmodule
