# Analysis Report: 3_double_reservoir_case

## 1. Problem Description
This report details the simulation results for the '3_double_reservoir_case' scenario.

## 2. Inputs
- **Topology File:** `examples/3_double_reservoir_case/topology.yml`
- **Disturbances File:** `examples/3_double_reservoir_case/disturbances.csv`
- **Control Parameters File:** `examples/3_double_reservoir_case/control_parameters.yaml`

## 3. Results

![Simulation Results](results/3_double_reservoir_case_results.png)

### 3.1. Performance Metrics
Performance metrics could not be calculated for this case.

### 3.2. Raw Data Sample
|   time |   tank1.storage |   tank2.storage |   pid_controller.output |
|-------:|----------------:|----------------:|------------------------:|
|      0 |          4.4    |         3.7     |                 2.6     |
|      1 |          6.94   |         3.6775  |                 2.98    |
|      2 |          9.2645 |         3.91181 |                 3.0185  |
|      3 |         10.8683 |         4.34929 |                 2.53029 |
|      4 |         11.4003 |         4.89246 |                 1.61883 |

## 4. Analysis and Discussion
- The controller exhibited an overshoot, suggesting the proportional or integral gain might be too high.
- A non-zero steady-state error was observed, which could indicate a need for integral action or adjustment of the 'I' gain.
- The system's response to disturbances can be seen in the plot, showing how the controller adapts to changes in inflow or demand.
