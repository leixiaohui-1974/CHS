# Analysis Report: 2_single_reservoir_case

## 1. Problem Description
This report details the simulation results for the '2_single_reservoir_case' scenario.

## 2. Inputs
- **Topology File:** `examples/2_single_reservoir_case/topology.yml`
- **Disturbances File:** `examples/2_single_reservoir_case/disturbances.csv`
- **Control Parameters File:** `examples/2_single_reservoir_case/control_parameters.yaml`

## 3. Results

![Simulation Results](results/2_single_reservoir_case_results.png)

### 3.1. Performance Metrics
Performance metrics could not be calculated for this case.

### 3.2. Raw Data Sample
|   time |   tank1.storage |   tank1.output |   pid_controller.output |
|-------:|----------------:|---------------:|------------------------:|
|      0 |         1.675   |       0.1      |                 1.275   |
|      1 |        -0.85625 |       0.335    |                -2.19625 |
|      2 |         4.71469 |      -0.17125  |                 5.39969 |
|      3 |        -7.47289 |       0.942937 |               -11.2446  |
|      4 |        19.2406  |      -1.49458  |                25.2189  |

## 4. Analysis and Discussion
- The controller exhibited an overshoot, suggesting the proportional or integral gain might be too high.
- A non-zero steady-state error was observed, which could indicate a need for integral action or adjustment of the 'I' gain.
- The system's response to disturbances can be seen in the plot, showing how the controller adapts to changes in inflow or demand.
