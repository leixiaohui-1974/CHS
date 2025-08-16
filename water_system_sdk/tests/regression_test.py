import numpy as np
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.main import SimulationEngine, SimulationMode
from chs_sdk.agents.body_agents import TankAgent
from chs_sdk.agents.disturbance_agents import InflowAgent
from chs_sdk.agents.message_bus import InMemoryMessageBus as MessageBus

def run_module_version(steps: int, area: float, initial_level: float, inflow_rate: float) -> float:
    """
    Runs the simulation using the direct module-level classes.
    """
    print("\n--- Running Module Version ---")
    tank = LinearTank(area=area, initial_level=initial_level)
    for i in range(steps):
        tank.input.inflow = inflow_rate
        tank.step(dt=1.0)
    final_level = tank.level
    print(f"Final level (Module Version): {final_level:.4f}")
    return final_level

def run_agent_version(steps: int, area: float, initial_level: float, inflow_rate: float) -> float:
    """
    Runs the simulation using the new Agent-based architecture.
    """
    print("--- Running Agent Version ---")
    message_bus = MessageBus()
    inflow_pattern = [inflow_rate] * steps

    inflow_agent = InflowAgent(
        agent_id="inflow_source", kernel=None, topic="inflow/tank1",
        rainfall_pattern=inflow_pattern
    )

    tank_agent = TankAgent(
        agent_id="tank1", kernel=None, area=area, initial_level=initial_level,
        inflow_topic="inflow/tank1",
        state_topic="state/tank1"
    )

    engine = SimulationEngine(
        mode=SimulationMode.SIL, agents=[inflow_agent, tank_agent], message_bus=message_bus
    )

    inflow_agent.kernel = engine
    tank_agent.kernel = engine

    inflow_agent.setup()
    tank_agent.setup()

    engine.run(duration_seconds=steps, time_step_seconds=1.0)

    final_level = tank_agent.model.level
    print(f"Final level (Agent Version): {final_level:.4f}")
    return final_level

def test_regression_versions_match():
    """
    This is the main regression test function that pytest will discover.
    It runs a simple scenario in both module and agent mode and asserts
    that the results are identical.
    """
    # Define simulation parameters
    SIM_STEPS = 10
    TANK_AREA = 100.0
    INITIAL_LEVEL = 5.0
    INFLOW_RATE = 10.0

    # Run both simulations
    module_result = run_module_version(SIM_STEPS, TANK_AREA, INITIAL_LEVEL, INFLOW_RATE)
    agent_result = run_agent_version(SIM_STEPS, TANK_AREA, INITIAL_LEVEL, INFLOW_RATE)

    # Compare the results
    print("\n--- Comparison ---")
    print(f"Module version final level: {module_result:.6f}")
    print(f"Agent version final level:  {agent_result:.6f}")

    assert np.isclose(module_result, agent_result), "Regression test failed: Results do not match!"

    print("\n✅ Regression test passed!")
