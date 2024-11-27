# How to verify the hardware grpah

This document describes how to verify the hardware graph, using vivado simulater.

if you use example dataset.
1. copy hw_input.txt bit data to /vivado_project/final_demo.sim/hw_input.mem
2. Run simulation. (change DATA_NUM parameter to the number of data in hw_input.mem)
3. Output data will be saved in /vivado_project/final_demo.sim/output_result.json
4. Run comp_graph.py script to compare sw_graph.json and output_result.json

if you want to use new dataset.
1. run make_graph.py script to generate sw graph.
2. run make_hw_input.py script to generate hw input and sw graph with json format. 
3. copy hw_input.txt bit data to /vivado_project/final_demo.sim/hw_input.mem
4. Open archived vivado project or create new one using HW directory.
5. Run simulation. (change DATA_NUM parameter to the number of data in hw_input.mem)
6. Output data will be saved in /vivado_project/final_demo.sim/output_result.json
7. Run comp_graph.py script to compare sw_graph.json and output_result.json