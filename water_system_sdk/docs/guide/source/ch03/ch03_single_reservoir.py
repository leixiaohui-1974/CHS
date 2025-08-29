import matplotlib.pyplot as plt

from chs_sdk.simulation_manager import SimulationManager
from chs_sdk.simulation_builder import SimulationBuilder
from chs_sdk.modules.modeling.storage_models import FirstOrderInertiaModel
from chs_sdk.modules.disturbances.predefined import Disturbance
from chs_sdk.modules.basic_tools.solvers import EulerIntegrator

def run_simulation():
    """
    This script demonstrates the basic setup and execution of a simulation
    for a single reservoir with a constant inflow.
    """
    # 1. Use the builder to construct the configuration fluently.
    builder = SimulationBuilder()
    sdk_config = (builder
        .set_simulation_params(total_time=24, dt=1.0)
        .add_component(
            name="MyReservoir",
            component_type="FirstOrderInertiaModel",
            params={"initial_storage": 10.0, "time_constant": 5.0, "solver_class": EulerIntegrator, "dt": 1.0}
        )
        .add_component(
            name="inflow",
            component_type="Disturbance",
            params={"signal_type": "constant", "value": 5.0}
        )
        .add_connection(
            source="inflow.output",
            target="MyReservoir.input.inflow"
        )
        .set_execution_order(["inflow", "MyReservoir"])
        .configure_logger([
            "MyReservoir.output",
            "MyReservoir.state.storage"
        ])
        .build()
    )

    # 2. Initialize and run the simulation
    manager = SimulationManager(config=sdk_config)
    results_df = manager.run()

    # 3. 可视化结果
    print("仿真结果:")
    print(results_df)

    plt.figure(figsize=(10, 6))
    plt.plot(results_df['time'], results_df['MyReservoir.state.storage'], label='水库蓄水量')
    plt.xlabel('时间 (小时)')
    plt.ylabel('蓄水量 (单位)')
    plt.title('水库仿真结果')
    plt.grid(True)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    run_simulation()
