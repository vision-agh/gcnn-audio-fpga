package graph_pkg;


    parameter F_RADIUS   = 10; //Search radius will be F_RADIUS*SKIPSTEPS                    
    parameter T_RADIUS   = 20000;                 
    parameter MAX_EDGES  = (F_RADIUS*2) + 1; //the same F neighbour possible!;         
    parameter PRECISION_GEN  = 16;                    
    parameter PRECISION_CONV1  = 16;                    
    parameter PRECISION_CONV2  = 8;                    
    parameter PRECISION_CONV3  = 8;                    
    parameter PRECISION_CONV4  = 8;                    

    parameter T_WIDTH  = 20; //Max of 1000000
    parameter F_WIDTH  = 10; //Max of 700
    
    parameter NUM_CHANNEL = 700;

    parameter INPUT_PARAMETER = 2; 
    
    parameter INPUT_DIM_1 = 2; 
    parameter OUTPUT_DIM_1 = 64;
    parameter OUTPUT_DIM_2 = 64;
    parameter OUTPUT_DIM_3 = 64;
    parameter OUTPUT_DIM_4 = 64;

    parameter ZERO_POINT = '0;
    parameter MULTIPLIER = '0;
   
    parameter SKIP_STEP = 10;
    
    typedef struct packed {
      logic [T_WIDTH -1: 0] t;
      logic [F_WIDTH -1: 0] f;
      logic                 is_last;
      logic                 valid;
    } event_type;

    typedef struct packed {
      logic [PRECISION_GEN-1 : 0] dt;
      logic                       is_connected;
    } edge_type;

    parameter DELTA_T_WIDTH = 15; //max value of 20000
    parameter GEN_MULTIPLIER_T = 4295;
    parameter GEN_MULTIPLIER_F = 6135480;
    parameter GEN_ZERO_POINT = '0;

    parameter CONV1_MULTIPLIER_DIFF_T = 214742;
    parameter CONV1_MULTIPLIER_OUT = 58670;
    parameter CONV1_ZERO_POINT_IN = '0;
    parameter CONV1_ZERO_POINT_OUT = 36533;
    parameter CONV1_ZERO_POINT_WEIGHT = 30075;
    parameter logic [15:0] CONV1_SCALE_IN [21:0] = { 32767, 29490, 26214, 22937,
                                                     19660, 16383, 13107, 9830, 
                                                     6553,  3277,  0,     65534,
                                                     62257, 58981, 55704, 52427,
                                                     49150, 45874, 42597, 39320, 
                                                     36044, 32767 };

    parameter CONV2_MULTIPLIER_DIFF_T = 214742;
    parameter CONV2_MULTIPLIER_OUT = 58670;
    parameter CONV2_ZERO_POINT_IN = '0;
    parameter CONV2_ZERO_POINT_OUT = 36533;
    parameter CONV2_ZERO_POINT_WEIGHT = 30075;
    parameter logic [15:0] CONV2_SCALE_IN [21:0] = { 32767, 29490, 26214, 22937,
                                                     19660, 16383, 13107, 9830, 
                                                     6553,  3277,  0,     65534,
                                                     62257, 58981, 55704, 52427,
                                                     49150, 45874, 42597, 39320, 
                                                     36044, 32767 };

    parameter CONV3_MULTIPLIER_DIFF_T = 214742;
    parameter CONV3_MULTIPLIER_OUT = 58670;
    parameter CONV3_ZERO_POINT_IN = '0;
    parameter CONV3_ZERO_POINT_OUT = 36533;
    parameter CONV3_ZERO_POINT_WEIGHT = 30075;
    parameter logic [7:0] CONV3_SCALE_IN [21:0] = { 32767, 29490, 26214, 22937,
                                                     19660, 16383, 13107, 9830, 
                                                     6553,  3277,  0,     65534,
                                                     62257, 58981, 55704, 52427,
                                                     49150, 45874, 42597, 39320, 
                                                     36044, 32767 };

    parameter CONV4_MULTIPLIER_DIFF_T = 214742;
    parameter CONV4_MULTIPLIER_OUT = 58670;
    parameter CONV4_ZERO_POINT_IN = '0;
    parameter CONV4_ZERO_POINT_OUT = 36533;
    parameter CONV4_ZERO_POINT_WEIGHT = 30075;
    parameter logic [7:0] CONV4_SCALE_IN [21:0] = { 32767, 29490, 26214, 22937,
                                                    19660, 16383, 13107, 9830, 
                                                    6553,  3277,  0,     65534,
                                                    62257, 58981, 55704, 52427,
                                                    49150, 45874, 42597, 39320, 
                                                    36044, 32767 };

endpackage