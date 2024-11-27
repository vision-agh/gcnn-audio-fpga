`timescale 1ns / 1ps

import graph_pkg::*;

parameter int DATA_NUM = 6575;

module tb_generate_graph;

    // Clock and reset signals
    logic clk;
    logic reset;

    // Inputs to generate_graph
    logic [T_WIDTH-1:0] t;
    logic [F_WIDTH-1:0] f;
    logic is_valid;

    // Outputs from generate_graph
    graph_event_type out_event;
    graph_edge_type [MAX_EDGES-1:0] out_edges;
    
    logic [T_WIDTH+F_WIDTH-1 : 0] mem [DATA_NUM-1 : 0];
    logic empty;

    integer outfile;
    integer mem_index;
    
    initial begin
        outfile = $fopen("/home/360/360.3-Stages/360.3.91-HN280727/gcn_audio/gcn_audio.sim/output_results.json", "w");
        $readmemb("/home/360/360.3-Stages/360.3.91-HN280727/gcn_audio/gcn_audio.sim/hw_input.mem", mem);

        // Write the beginning of the JSON array
        $fwrite(outfile, "[\n");
    end

    // Instantiate the generate_graph module
    generate_graph uut (
        .clk(clk),
        .reset(reset),
        .t(t),
        .f(f),
        .is_valid(is_valid),
        .out_event(out_event),
        .out_edges(out_edges)
    );

    // Clock generation
    always begin
        clk = 0;
        forever #5 clk = ~clk; // 100MHz clock
    end

    // Monitor and write pos_item and edges to the output file
    always @(posedge clk) begin
        if (out_event.valid == 1'b1) begin
            $fwrite(outfile, "  {\n");
            $fwrite(outfile, "    \"pos_item\": {\"t\": %0d, \"f\": %0d},\n",
                (out_event.t < 0) ? -out_event.t : out_event.t,
                (out_event.f < 0) ? -out_event.f : out_event.f);
            
            $fwrite(outfile, "    \"edges\": [\n");
        
            // Write each edge structure to the output file
            for (int j=0; j<MAX_EDGES; j=j+1) begin
                if(out_edges[j].is_connected) begin
                    $fwrite(outfile, "      {\"t\": %0d, \"f\": %0d, \"dt\": %0d, \"df\": %0d}",
                        out_edges[j].t, 
                        out_edges[j].f, 
                        (out_edges[j].dt < 0) ? -out_edges[j].dt : out_edges[j].dt,
                        (out_edges[j].df < 0) ? -out_edges[j].df : out_edges[j].df);

                    // Add a comma unless it's the last connected edge
                    if (j < MAX_EDGES - 1) begin
                        for (int k=j+1; k<MAX_EDGES; k=k+1) begin
                            if(out_edges[k].is_connected) begin
                                $fwrite(outfile, ",\n");
                                break;
                            end
                        end
                    end else begin
                        $fwrite(outfile, "\n");
                    end
                end
            end
            
            $fwrite(outfile, "    ]\n  },\n");
        end
    end

    // Reset generation
    initial begin

        reset = 1;
        is_valid = 0;
        mem_index = 0;
        #20;
        reset = 0;
        empty = 0;
        #20

        @(posedge clk);
        is_valid = 0;

        while (mem_index < DATA_NUM) begin 
            @(posedge clk);
                {t, f} = mem[mem_index]; 
                mem_index = mem_index + 1;
                is_valid = 1;
        end

        // Deassert is_valid
        @(posedge clk);
        is_valid = 0;

        // Finish simulation
        #1000000;
        $finish;
    end
    
    // Close the file at the end of the simulation
    final begin
        // Remove the trailing comma from the last JSON object
        $fseek(outfile, -3, 2); // Adjusted offset to handle the last comma
        $fwrite(outfile, "  }\n]\n"); // Close the JSON array properly
        $fclose(outfile);
    end

endmodule