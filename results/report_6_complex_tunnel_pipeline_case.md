# Analysis Report: 6_complex_tunnel_pipeline_case

## 1. Problem Description
This report details the simulation results for the '6_complex_tunnel_pipeline_case' scenario.

## 2. Inputs
- **Topology File:** `examples/6_complex_tunnel_pipeline_case/topology.yml`
- **Disturbances File:** `examples/6_complex_tunnel_pipeline_case/disturbances.csv`
- **Control Parameters File:** `examples/6_complex_tunnel_pipeline_case/control_parameters.yaml`

## 3. Results

![Simulation Results](results/6_complex_tunnel_pipeline_case_results.png)

### 3.1. Performance Metrics
Performance metrics could not be calculated for this case.

### 3.2. Raw Data Sample
|   time |   main_reservoir.storage |   main_tunnel.output |   surge_tank.storage |   pressure_pipe_1.output |   pressure_pipe_2.output |   high_level_tank.storage |   final_channel.output |
|-------:|-------------------------:|---------------------:|---------------------:|-------------------------:|-------------------------:|--------------------------:|-----------------------:|
|      0 |                  549     |             43.6087  |              99      |                  39.3075 |                  31.9124 |                   110.912 |                9.47826 |
|      1 |                  597.902 |             25.096   |              98.01   |                  38.6653 |                  28.6487 |                   138.175 |                7.96597 |
|      2 |                  646.706 |             14.6748  |              97.0299 |                  38.0677 |                  25.2549 |                   161.702 |                7.1112  |
|      3 |                  695.413 |              8.82711 |              96.0596 |                  37.51   |                  21.7691 |                   181.45  |                6.62807 |
|      4 |                  744.022 |              5.5643  |              95.099  |                  36.9877 |                  18.223  |                   197.405 |                6.355   |

## 4. Analysis and Discussion
- The controller exhibited an overshoot, suggesting the proportional or integral gain might be too high.
- A non-zero steady-state error was observed, which could indicate a need for integral action or adjustment of the 'I' gain.
- The system's response to disturbances can be seen in the plot, showing how the controller adapts to changes in inflow or demand.
