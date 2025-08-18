import matplotlib.pyplot as plt
import os
import pandas as pd

# This assumes the package is installed. If not, you might need to adjust the python path.
from chs_sdk.simulation_manager import SimulationManager

def main():
    """
    This example demonstrates how to run a simulation for a single reservoir
    with a constant inflow using the SimulationManager.
    """
    # 1. Define the simulation configuration as a Python dictionary.
    simulation_config = {
        'solver': 'RK4Integrator',
        'dt': 1.0,
        'duration': 24,
        'components': [
            {
                'name': 'inflow',
                'type': 'Disturbance',
                'properties': {
                    'signal_type': 'constant',
                    'value': 5.0
                }
            },
            {
                'name': 'MyReservoir',
                'type': 'FirstOrderInertiaModel',
                'properties': {
                    'initial_storage': 10.0,
                    'time_constant': 5.0
                },
                'connections': {
                    'inflow': 'inflow.output'
                }
            }
        ],
        'execution_order': [
            'inflow',
            'MyReservoir'
        ],
        'logger_config': [
            'MyReservoir.state.storage',
            'inflow.output'
        ],
        'simulation_params': {
            'total_time': 24,
            'dt': 1.0
        }
    }

    # 2. Instantiate SimulationManager with the configuration dictionary.
    manager = SimulationManager(config=simulation_config)

    # 3. Run the simulation.
    results_df = manager.run()

    # 4. Process and plot the results.
    print("\nSimulation Results (first 5 rows):")
    print(results_df.head())

    if not os.path.exists('results'):
        os.makedirs('results')

    plt.figure(figsize=(10, 6))
    plt.plot(results_df['time'], results_df['MyReservoir.state.storage'], label='Reservoir Storage')
    plt.xlabel('Time (hours)')
    plt.ylabel('Storage (units)')
    plt.title('Reservoir Simulation Results')
    plt.grid(True)
    plt.legend()

    plot_filename = 'results/ch03_single_reservoir.png'
    plt.savefig(plot_filename)
    print(f"\nPlot saved to {plot_filename}")
    # plt.show() # plt.show() will block the execution, use plt.savefig() instead

if __name__ == "__main__":
    main()
