# Unit tests for Body Agents

import pytest
import numpy as np
from unittest.mock import MagicMock

# Import the agent classes
from water_system_simulator.agents import LinearTankAgent, PipelineAgent, PumpingStationAgent
from water_system_simulator.agents.base import EmbodiedAgent

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
    initial_level = 10.0
    area = 100.0
    tank_agent = LinearTankAgent(
        id="test_tank",
        area=area,
        initial_level=initial_level,
    )
    model = tank_agent.core_physics_model

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
    assert abs(model.level - expected_new_level) < 1e-6, "Water level should update according to mass balance"

    # 5. Simulate a few more steps
    steps = 5
    current_level = model.level
    for _ in range(steps):
        model.step(dt)

    final_expected_level = current_level + (expected_level_change * steps)
    assert abs(model.level - final_expected_level) < 1e-6, "Water level should update linearly over multiple steps"


def test_pipeline_agent_steady_state_flow_ut_ba_03():
    """
    Tests UT-BA-03: Verifies the steady-state flow calculation for PipelineAgent's model.
    """
    # 1. Setup
    length = 1000.0  # m
    diameter = 1.0  # m
    friction = 0.02 # dimensionless

    pipeline_agent = PipelineAgent(
        id="test_pipe",
        length=length,
        diameter=diameter,
        friction_factor=friction,
    )
    model = pipeline_agent.core_physics_model

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
    # F = aH^2 + bH + c. Let's make a simple curve: F = -0.1*H^2 + 0*H + 10
    from water_system_simulator.modeling.pump_models import CentrifugalPump
    # F = aH^2 + bH + c. Let's make a simple curve: F = -0.1*H^2 + 0*H + 10
    # This means at 0 head, flow is 10. At 10m head, flow is 0.

    hq_curve = lambda q: -0.1 * q**2 + 10
    eff_q_curve = lambda q: 0.8

    pump1 = CentrifugalPump(hq_curve=hq_curve, eff_q_curve=eff_q_curve, name="pump1")
    pump2 = CentrifugalPump(hq_curve=hq_curve, eff_q_curve=eff_q_curve, name="pump2")


    pump_agent = PumpingStationAgent(
        id="test_pump",
        pumps=[pump1, pump2]
    )
    model = pump_agent.core_physics_model

    # 2. Test with 1 pump
    inlet_pressure = 10.0 # m
    outlet_pressure = 15.0 # m
    head_diff = outlet_pressure - inlet_pressure # 5.0 m

    pump1.set_speed(1.0)
    pump2.set_speed(0.0)

    model.step(system_head=head_diff, dt=1.0)

    # 3. Calculate theoretical flow
    # For H=5, Q should be sqrt(50) = 7.07
    expected_flow_one_pump = np.sqrt(50)

    # 4. Verify
    assert abs(model.total_flow - expected_flow_one_pump) < 0.05, "Flow for one pump should match the curve"

    # 5. Test with 2 pumps
    pump1.set_speed(1.0)
    pump2.set_speed(1.0)
    model.step(system_head=head_diff, dt=1.0)
    expected_flow_two_pumps = expected_flow_one_pump * 2
    assert abs(model.total_flow - expected_flow_two_pumps) < 0.1, "Flow should scale linearly with number of pumps"
