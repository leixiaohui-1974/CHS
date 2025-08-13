import matplotlib.pyplot as plt
import os

# This assumes the package is installed. If not, you might need to adjust the python path.
from water_system_simulator.simulation_manager import SimulationManager

def main():
    """
    This example demonstrates how to run a simulation using the SDK
    by providing a configuration dictionary directly to the SimulationManager.
    """
    # 1. Define the entire simulation configuration as a Python dictionary.
    simulation_config = {
        'topology': {
            'solver': 'RK4Integrator',
            'dt': 1.0,
            'duration': 120,
            'components': [
                {
                    # A virtual component to represent the external inflow disturbance.
                    # The name 'external_inflow' MUST match the column name in the disturbance data.
                    'name': 'external_inflow',
                    'type': 'Disturbance'
                },
                {
                    'name': 'pid_controller',
                    'type': 'PIDController',
                    'connections': {
                        # The controller uses the tank's storage from the previous time step.
                        'measured_value': 'tank1.storage'
                    }
                },
                {
                    # This sums the controller's output and the disturbance.
                    # It must be processed after the components it connects to.
                    'name': 'inflow_junction',
                    'type': 'SummingPoint',
                    'connections': ['pid_controller.output', 'external_inflow.output'],
                    'gains': [1.0, 1.0]
                },
                {
                    # The tank uses the output of the junction as its inflow.
                    # It must be processed after the junction.
                    'name': 'tank1',
                    'type': 'FirstOrderInertiaModel',
                    'properties': {
                        'initial_storage': 0.5,
                        'time_constant': 5.0
                    },
                    'connections': {
                        'inflow': 'inflow_junction.output'
                    }
                }
            ],
            'logging': [
                'time',
                'tank1.storage',
                'tank1.output',
                'pid_controller.output'
            ]
        },
        'control_params': {
            'pid_controller_params': {
                'kp': 1.5,
                'ki': 0.05,
                'kd': 1.0,
                'setpoint': 1.0
            }
        },
        'disturbances': [
            {'time': 0, 'external_inflow': 0.0},
            {'time': 60, 'external_inflow': 0.2},
            {'time': 80, 'external_inflow': 0.0}
        ]
    }

    # 2. Instantiate SimulationManager with the configuration dictionary.
    manager = SimulationManager(config=simulation_config)

    # 3. Run the simulation.
    # The duration can also be specified in the config dictionary.
    duration = simulation_config['topology'].get('duration', 200)
    results_df = manager.run(duration=duration)

    # 4. Process and plot the results.
    print("\nSimulation Results (first 5 rows):")
    print(results_df.head())

    if not os.path.exists('results'):
        os.makedirs('results')

    plt.figure(figsize=(12, 8))

    plt.subplot(2, 1, 1)
    plt.plot(results_df['time'], results_df['tank1.storage'], label='Tank Storage')
    plt.axhline(y=1.0, color='r', linestyle='--', label='Setpoint')
    plt.title('Reservoir Storage Level')
    plt.ylabel('Storage')
    plt.legend()
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.plot(results_df['time'], results_df['pid_controller.output'], label='PID Output (Inflow)')
    plt.title('Controller Output')
    plt.ylabel('Flow')
    plt.xlabel('Time (s)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plot_filename = 'results/sdk_single_reservoir_simulation.png'
    plt.savefig(plot_filename)
    print(f"\nPlot saved to {plot_filename}")


if __name__ == "__main__":
    main()
