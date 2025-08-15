# Unit tests for Body Agents

import pytest
import numpy as np
from unittest.mock import MagicMock

# Import the agent classes
from water_system_sdk.src.chs_sdk.agents.body_agents import TankAgent, PipeAgent, PumpAgent

# A mock kernel class for agent instantiation
class MockKernel:
    def __init__(self):
        self.message_bus = MagicMock()
        self.time_step = 1.0
        self.current_time = 0.0

def test_tank_agent_mass_balance_ut_ba_01():
    """
    Tests UT-BA-01: Verifies the mass balance equation for TankAgent's model.
    """
    # 1. Setup
    mock_kernel = MockKernel()
    initial_level = 10.0
    area = 100.0
    tank_agent = TankAgent(
        agent_id="test_tank",
        kernel=mock_kernel,
        area=area,
        initial_level=initial_level,
        config={} # Add empty config
    )
    model = tank_agent.model

    # 2. Set constant inflow
    inflow_rate = 10.0  # m^3/s
    model.input.inflow = inflow_rate
    model.input.release_outflow = 0.0
    model.input.demand_outflow = 0.0

    # 3. Simulate one step
    dt = 1.0
    model.step(dt)

    # 4. Verify
    expected_level_change = (inflow_rate / area) * dt
    expected_new_level = initial_level + expected_level_change
    assert abs(model.state.level - expected_new_level) < 1e-6, "Water level should update according to mass balance"

    # 5. Simulate a few more steps
    steps = 5
    current_level = model.state.level
    for _ in range(steps):
        model.step(dt)

    final_expected_level = current_level + (expected_level_change * steps)
    assert abs(model.state.level - final_expected_level) < 1e-6, "Water level should update linearly over multiple steps"


def test_pipe_agent_steady_state_flow_ut_ba_03():
    """
    Tests UT-BA-03: Verifies the steady-state flow calculation for PipeAgent's model.
    """
    # 1. Setup
    mock_kernel = MockKernel()
    length = 1000.0  # m
    diameter = 1.0  # m
    friction = 0.02 # dimensionless

    # PipeAgent requires topics in its config for setup
    config = {
        "inlet_pressure_topic": "p_in",
        "outlet_pressure_topic": "p_out",
        "state_topic": "pipe_state"
    }

    pipe_agent = PipeAgent(
        agent_id="test_pipe",
        kernel=mock_kernel,
        length=length,
        diameter=diameter,
        friction_factor=friction,
        inlet_pressure_topic=config["inlet_pressure_topic"],
        outlet_pressure_topic=config["outlet_pressure_topic"],
        state_topic=config["state_topic"],
        config=config
    )
    model = pipe_agent.model

    # 2. Set fixed pressure difference
    inlet_pressure = 50.0 # m head
    outlet_pressure = 45.0 # m head
    delta_h = inlet_pressure - outlet_pressure

    # 3. Simulate until flow stabilizes
    # Run for a long time to ensure steady state is reached
    for _ in range(2000):
        model.step(inlet_pressure, outlet_pressure, dt=1.0)

    simulated_flow = model.flow

    # 4. Calculate theoretical flow
    g = 9.81
    area = np.pi * (diameter**2) / 4.0
    # from h_f = f * (L/D) * (v^2 / 2g) => v = sqrt( (h_f * D * 2g) / (f * L) )
    theoretical_velocity = np.sqrt((delta_h * diameter * 2 * g) / (friction * length))
    theoretical_flow = theoretical_velocity * area

    # 5. Verify
    assert abs(simulated_flow - theoretical_flow) < 1e-3, f"Simulated flow ({simulated_flow}) should match theoretical steady-state flow ({theoretical_flow})"


def test_pump_agent_flow_calculation_ut_ba_04():
    """
    Tests UT-BA-04: Verifies the flow calculation for PumpAgent's model.
    """
    # 1. Setup
    mock_kernel = MockKernel()
    # F = aH^2 + bH + c. Let's make a simple curve: F = -0.1*H^2 + 0*H + 10
    # This means at 0 head, flow is 10. At 10m head, flow is 0.
    curve_coeffs = [-0.05, 0.1, 8] # A more realistic curve F = -0.05H^2 + 0.1H + 8

    config = {
        "inlet_pressure_topic": "p_in",
        "outlet_pressure_topic": "p_out",
        "num_pumps_on_topic": "pumps_on",
        "state_topic": "pump_state"
    }

    pump_agent = PumpAgent(
        agent_id="test_pump",
        kernel=mock_kernel,
        num_pumps_total=4,
        curve_coeffs=curve_coeffs,
        inlet_pressure_topic=config["inlet_pressure_topic"],
        outlet_pressure_topic=config["outlet_pressure_topic"],
        num_pumps_on_topic=config["num_pumps_on_topic"],
        state_topic=config["state_topic"],
        initial_num_pumps_on=1,
        config=config
    )
    model = pump_agent.model

    # 2. Test with 1 pump
    inlet_pressure = 10.0 # m
    outlet_pressure = 15.0 # m
    head_diff = outlet_pressure - inlet_pressure # 5.0 m

    model.step(inlet_pressure, outlet_pressure, num_pumps_on=1)

    # 3. Calculate theoretical flow
    a, b, c = curve_coeffs
    expected_flow_one_pump = a * head_diff**2 + b * head_diff + c

    # 4. Verify
    assert abs(model.flow - expected_flow_one_pump) < 1e-6, "Flow for one pump should match the curve"

    # 5. Test with 2 pumps
    model.step(inlet_pressure, outlet_pressure, num_pumps_on=2)
    expected_flow_two_pumps = expected_flow_one_pump * 2
    assert abs(model.flow - expected_flow_two_pumps) < 1e-6, "Flow should scale linearly with number of pumps"
