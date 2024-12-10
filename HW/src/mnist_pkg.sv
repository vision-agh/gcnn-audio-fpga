package graph_pkg;


    parameter F_RADIUS   = 10; //Search radius will be F_RADIUS*SKIPSTEPS                    
    parameter T_RADIUS   = 20972;                 
    parameter MAX_EDGES  = F_RADIUS*2;         
    parameter PRECISION  = 8;                    
    
    parameter T_WIDTH  = 21; //20+1
    parameter F_WIDTH  = 21;
    
    parameter NUM_CHANNEL = 700;
    
    parameter SCALE = 15;

    parameter INPUT_PARAMETER = 2; 
    
    parameter INPUT_DIM_1 = 4; 
    parameter OUTPUT_DIM_1 = 64;

    // parameter INPUT_DIM_2 = OUTPUT_DIM_1 + INPUT_PARAMETER; 
    // parameter OUTPUT_DIM_2 = 32;

    // parameter INPUT_DIM_3 = OUTPUT_DIM_2 + INPUT_PARAMETER; 
    // parameter OUTPUT_DIM_3 = 32;

    // parameter INPUT_DIM_4 = OUTPUT_DIM_3 + INPUT_PARAMETER;; 
    // parameter OUTPUT_DIM_4 = 32;

    // parameter INPUT_DIM_5 = OUTPUT_DIM_4 + INPUT_PARAMETER;; 
    // parameter OUTPUT_DIM_5 = 32;

    parameter ZERO_POINT = '0;
    parameter MULTIPLIER = '0;

    parameter N_WIDTH = 14;
    
    parameter SKIP_STEP = 10;

    typedef struct packed {
      logic signed [T_WIDTH -1: 0] t;
      logic signed [F_WIDTH -1: 0] f;
      logic                         valid;
    } graph_event_type;
    
    typedef struct packed {
      logic signed [T_WIDTH-1 : 0] t;
      logic signed [F_WIDTH-1 : 0] f;
      logic signed [T_WIDTH-1 : 0] dt;
      logic signed [F_WIDTH-1 : 0] df;
      logic                      is_connected;
    } graph_edge_type;
    
    typedef struct packed {
      logic signed [T_WIDTH -1: 0] t;
      logic signed [F_WIDTH -1: 0] f;
      logic                         valid;
    } event_type;
    
    typedef struct packed {
      logic signed [T_WIDTH-1 : 0] dt;
      logic                      is_connected;
    } edge_type;

    parameter MEMORY_OPS_NUM = F_RADIUS + 1; 

endpackage