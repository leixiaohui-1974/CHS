import pytest
from water_system_simulator.simulation_manager import SimulationManager, getattr_by_path, setattr_by_path
from water_system_simulator.modeling.storage_models import ReservoirModel
from water_system_simulator.control.pid_controller import PIDController

@pytest.fixture
def simple_pid_config():
    """Provides a basic config for a reservoir and a PID controller."""
    return {
        "simulation_params": {"total_time": 1, "dt": 0.1},
        "components": {
            "reservoir_A": {
                "type": "ReservoirModel",
                "properties": {"area": 1.0, "initial_level": 5.0}
            },
            "pid_controller": {
                "type": "PIDController",
                "properties": {"Kp": 1, "Ki": 1, "Kd": 1, "set_point": 10.0}
            }
        },
        "connections": [
            {
                "source": "reservoir_A.output",
                "target": "pid_controller.input.error_source"
            }
        ],
        "execution_order": [
            {
                "component": "pid_controller",
                "method": "step",
                "args": {"dt": "simulation.dt"},
                "result_to": "reservoir_A.input.inflow"
            },
            {
                "component": "reservoir_A",
                "method": "step",
                "args": {"dt": "simulation.dt"}
            }
        ],
        "logger_config": ["reservoir_A.output"]
    }

def test_component_creation(simple_pid_config):
    """
    Tests if the SimulationManager correctly creates component instances
    based on the configuration dictionary.
    """
    manager = SimulationManager(config=simple_pid_config)
    manager.run() # The run method internally calls _build_system

    # Assert that the components dictionary is not empty
    assert manager.components
    # Assert that the specific components were created
    assert "reservoir_A" in manager.components
    assert "pid_controller" in manager.components
    # Assert that the created components are of the correct type
    assert isinstance(manager.components["reservoir_A"], ReservoirModel)
    assert isinstance(manager.components["pid_controller"], PIDController)

def test_connection_data_flow(simple_pid_config):
    """
    Tests if data flows correctly between components as defined in the
    'connections' part of the configuration.
    """
    manager = SimulationManager()

    # Manually build the system without running the full loop
    manager.config = simple_pid_config
    manager._build_system()

    # Get initial state of the reservoir
    initial_level = manager.components["reservoir_A"].output
    assert initial_level == 5.0

    # Manually process connections for the first step
    for conn in manager.config.get("connections", []):
        source_comp_name, source_attr_path = conn["source"].split('.', 1)
        target_comp_name, target_attr_path = conn["target"].split('.', 1)
        value = getattr_by_path(manager.components[source_comp_name], source_attr_path)
        setattr_by_path(manager.components[target_comp_name], target_attr_path, value)

    # Assert that the PID controller's input has been updated
    # with the reservoir's initial level.
    pid_input = manager.components["pid_controller"].input.error_source
    assert pid_input == initial_level
