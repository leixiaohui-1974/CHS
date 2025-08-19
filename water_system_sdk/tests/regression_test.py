import numpy as np
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.core.host import AgentKernel
from chs_sdk.modules.disturbances.timeseries_disturbance import TimeSeriesDisturbance
from docs.guide.source.project_utils import ModelAgent

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
    host = AgentKernel()

    host.add_agent(
        agent_class=ModelAgent,
        agent_id='tank1',
        model_class=LinearTank,
        area=area,
        initial_level=initial_level
    )

    host.add_agent(
        agent_class=ModelAgent,
        agent_id='inflow_source',
        model_class=TimeSeriesDisturbance,
        times=[0, steps],
        values=[inflow_rate, inflow_rate]
    )

    tank_agent = host._agents['tank1']
    inflow_agent = host._agents['inflow_source']

    tank_agent.subscribe(f"{inflow_agent.agent_id}/output", 'inflow')

    host.start(time_step=1.0)
    for _ in range(steps):
        inflow_agent.on_execute(host.current_time, host.time_step)
        host.message_bus.dispatch()
        tank_agent.on_execute(host.current_time, host.time_step)
        host.current_time += host.time_step

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
