import pytest
from unittest.mock import MagicMock
import numpy as np

from water_system_simulator.agents import (
    LinearTankAgent,
    PipelineAgent,
    PumpingStationAgent,
)
from water_system_simulator.agents.control_agents import (
    PIDControllerAgent,
    RuleBasedOperationalControllerAgent,
    MPCControllerAgent,
)
from water_system_simulator.agents.disturbance_agents import (
    RainfallAgent,
    WaterConsumptionAgent,
)
from water_system_simulator.modeling.pump_models import CentrifugalPump

def test_linear_tank_agent_creation():
    """Tests that a LinearTankAgent can be created."""
    agent = LinearTankAgent(id="tank1", area=100, initial_level=10)
    assert agent.id == "tank1"
    assert agent.core_physics_model is not None

def test_pipeline_agent_creation():
    """Tests that a PipelineAgent can be created."""
    agent = PipelineAgent(id="pipe1", length=1000, diameter=1)
    assert agent.id == "pipe1"
    assert agent.core_physics_model is not None

def test_pumping_station_agent_creation():
    """Tests that a PumpingStationAgent can be created."""
    hq_curve = lambda q: -0.1 * q**2 + 10
    eff_q_curve = lambda q: 0.8
    pump = CentrifugalPump(hq_curve=hq_curve, eff_q_curve=eff_q_curve, name="pump1")
    agent = PumpingStationAgent(id="pump_station1", pumps=[pump])
    assert agent.id == "pump_station1"
    assert agent.core_physics_model is not None

def test_pid_controller_agent_creation():
    """Tests that a PIDControllerAgent can be created."""
    agent = PIDControllerAgent(id="pid1", Kp=1, Ki=0.1, Kd=0.01, set_point=10)
    assert agent.id == "pid1"
    assert agent.controller is not None

def test_rule_based_controller_agent_creation():
    """Tests that a RuleBasedOperationalControllerAgent can be created."""
    rules = [{"if": [{"variable": "tank1.state.level", "operator": ">", "value": 12}], "then": {"pump1": "off"}}]
    agent = RuleBasedOperationalControllerAgent(id="rbc1", rules=rules, default_actions={})
    assert agent.id == "rbc1"
    assert agent.controller is not None

def test_rainfall_agent_creation():
    """Tests that a RainfallAgent can be created."""
    agent = RainfallAgent(id="rainfall1", rainfall_pattern=[1, 2, 3])
    assert agent.id == "rainfall1"
    assert agent.rainfall_model is not None

def test_water_consumption_agent_creation():
    """Tests that a WaterConsumptionAgent can be created."""
    agent = WaterConsumptionAgent(id="wc1", consumption_pattern=[1, 2, 3])
    assert agent.id == "wc1"
    assert agent.consumption_model is not None
