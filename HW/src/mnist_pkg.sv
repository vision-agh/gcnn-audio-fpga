package graph_pkg;

    //////////////////////////////
    // CONFIGURATION PARAMETERS //
    //////////////////////////////

//    parameter GRAPH_SIZE       = 1024;                  // The size of graph representation (in x, y and time dimensions)
//    parameter GRAPH_BIT_WIDTH  = $clog2(GRAPH_SIZE);
    parameter F_RADIUS           = 10;                    // The search radius for egde generation
    parameter T_RADIUS           = 20972;                    // The search radius for egde generation 2**16 * 0.02
    parameter MAX_EDGES                 = F_RADIUS*2;                   // The maximum number of edges for single vertice (before graph rescaling - MaxPool)
//    parameter PRECISION        = 25;                    // Precision for weights and features in GCNN model (in bits)
    parameter PRECISION        = 8;                    // Precision for weights and features in GCNN model (in bits)
    parameter string REPO_PATH = "/home/360/360.3-Stages/360.3.91-HN280727/gcnn-dvs-fpga";      // Path to repository (needed for memory init files)
    
//    parameter T_WIDTH  = 25; //8 + 16 + 1
    parameter T_WIDTH  = 21; //8 + 16 + 1
//    parameter F_WIDTH  = 25;
    parameter F_WIDTH  = 21;
    
    parameter NUM_CHANNEL = 700;
    
    parameter SCALE = 15;
//    parameter SCALE = 16;

    //matrix multiplication
    parameter INPUT_PARAMETER = 2; //dt,df
    
    parameter INPUT_DIM_1 = 4; 
    parameter OUTPUT_DIM_1 = 32;
    
    parameter INPUT_DIM_2 = OUTPUT_DIM_1 + INPUT_PARAMETER; 
    parameter OUTPUT_DIM_2 = 32;
    
    parameter INPUT_DIM_3 = OUTPUT_DIM_2 + INPUT_PARAMETER; 
    parameter OUTPUT_DIM_3 = 32;
    
    parameter INPUT_DIM_4 = OUTPUT_DIM_3 + INPUT_PARAMETER;; 
    parameter OUTPUT_DIM_4 = 32;
    
    parameter INPUT_DIM_5 = OUTPUT_DIM_4 + INPUT_PARAMETER;; 
    parameter OUTPUT_DIM_5 = 32;
    
    
    parameter ZERO_POINT = '0;
    parameter MULTIPLIER = '0;
    
//    parameter MAX_EVENT_NUM = 13000; //2 ** 14
//    parameter N_WIDTH = $clog2(MAX_EVENT_NUM);
    parameter N_WIDTH = 14;
    
//    parameter DATA_WIDTH_1 = T_WIDTH;
//    parameter DATA_WIDTH_2 = T_WIDTH+PRECISION;
//    parameter DATA_WIDTH_3 = T_WIDTH+2*PRECISION;
//    parameter DATA_WIDTH_4 = T_WIDTH+3*PRECISION;
//    parameter DATA_WIDTH_5 = T_WIDTH+4*PRECISION;
    
//    parameter OUTPUT_WIDTH_1 = T_WIDTH+PRECISION;
//    parameter OUTPUT_WIDTH_2 = T_WIDTH+2*PRECISION;
//    parameter OUTPUT_WIDTH_3 = T_WIDTH+3*PRECISION;
//    parameter OUTPUT_WIDTH_4 = T_WIDTH+4*PRECISION;

    
    
    ////////////////
    // DATA TYPES //
    ////////////////

    // event_type for normalized events processing
    typedef struct packed {
      logic signed [T_WIDTH -1: 0] t;
      logic signed [F_WIDTH -1: 0] f;
//      logic        [N_WIDTH-1 : 0] n;
      logic                         valid;
    } event_type;
    
    // edge_type for processing egde list (before graph rescaling - MaxPool)
    typedef struct packed {
      logic signed [T_WIDTH-1 : 0] t;
      logic signed [F_WIDTH-1 : 0] f;
      logic signed [T_WIDTH-1 : 0] dt;
      logic signed [F_WIDTH-1 : 0] df;
//      logic        [N_WIDTH-1 : 0] n;
      logic                      is_connected;
    } edge_type;


    ///////////////////////////////
    // CONTEXT MEMORY PARAMETERS //
    ///////////////////////////////

    parameter MEMORY_OPS_NUM = F_RADIUS + 1;   // Number of memory accesses for single event (before graph rescaling - MaxPool)

endpackage