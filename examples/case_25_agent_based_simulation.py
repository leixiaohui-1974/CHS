import logging
import time
from typing import Dict, Any, Optional

# This assumes the script is run with PYTHONPATH pointing to the 'src' directory, e.g.,
# PYTHONPATH=water_system_sdk/src python examples/case_25_agent_based_simulation.py
from water_system_simulator.agent.base_agent import BaseAgent, EmbodiedAgent
from water_system_simulator.agent.communication import MessageBus
from water_system_simulator.main import SimulationEngine, SimulationMode
from water_system_simulator.modeling.base_model import BaseModel

# --- 1. Define a simple physical model for a water tank ---
class WaterTankModel(BaseModel):
    """A simple stateful model of a water tank."""
    def __init__(self, id: str, area: float = 10.0, level: float = 5.0, **kwargs):
        super().__init__(id=id, **kwargs)
        self.area = area
        self.level = level
        self.inflow = 0.0
        self.outflow = 0.0

    def step(self, dt: float, **kwargs):
        # Update state based on inputs. In a real model, these might be complex equations.
        self.inflow = kwargs.get('inflow', self.inflow)
        self.outflow = kwargs.get('outflow', self.outflow)

        volume_change = (self.inflow - self.outflow) * dt
        level_change = volume_change / self.area
        self.level += level_change

    def get_state(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "inflow": self.inflow,
            "outflow": self.outflow
        }

# --- 2. Define the Agents for the simulation ---

class TankBodyAgent(EmbodiedAgent):
    """A Body Agent representing the physical water tank. It wraps the WaterTankModel."""
    def __init__(self, id: str, message_bus: MessageBus, model: WaterTankModel, **kwargs):
        super().__init__(id=id, message_bus=message_bus, core_model=model, **kwargs)
        # This agent listens for commands that affect its physical state.
        self.message_bus.subscribe(f"{self.id}.inflow.command", self.handle_inflow)
        self.message_bus.subscribe(f"{self.id}.outflow.command", self.handle_outflow_command)

    def handle_inflow(self, inflow_rate: float):
        # In a real model, this might be a complex process. Here we just set it.
        self.core_physics_model.inflow = inflow_rate

    def handle_outflow_command(self, outflow_rate: float):
        # The agent can enforce physical constraints.
        self.core_physics_model.outflow = max(0, outflow_rate)

    def step(self, dt: float, **kwargs):
        # The core model step is now primarily driven by messages handled by the agent.
        # We pass the model's current inputs to its step method.
        super().step(dt, inputs={
            "inflow": self.core_physics_model.inflow,
            "outflow": self.core_physics_model.outflow
        })
        # After stepping, the agent publishes its new state for others to see.
        state = self.get_state()
        self.message_bus.publish(f"{self.id}.state", state, sender_id=self.id)
        logging.info(f"Tank '{self.id}' state: Level={state['level']:.2f}m")


class InflowDisturbanceAgent(BaseAgent):
    """A Disturbance Agent that simulates a constant inflow to the tank."""
    def __init__(self, id: str, message_bus: MessageBus, target_topic: str, inflow_rate: float, **kwargs):
        super().__init__(id=id, message_bus=message_bus, **kwargs)
        self.target_topic = target_topic
        self.inflow_rate = inflow_rate

    def step(self, dt: float, **kwargs):
        # In each step, this agent simply publishes the inflow value.
        self.message_bus.publish(self.target_topic, self.inflow_rate, sender_id=self.id)
        logging.debug(f"Disturbance '{self.id}' published inflow of {self.inflow_rate}")


class ProportionalControlAgent(BaseAgent):
    """A simple Control Agent that tries to maintain a target water level."""
    def __init__(self, id: str, message_bus: MessageBus, state_topic: str, command_topic: str, setpoint: float, gain: float, **kwargs):
        super().__init__(id=id, message_bus=message_bus, **kwargs)
        self.state_topic = state_topic
        self.command_topic = command_topic
        self.setpoint = setpoint
        self.gain = gain
        self.current_level = 0.0 # The controller's belief of the current level

        self.message_bus.subscribe(self.state_topic, self.handle_state_update)

    def handle_state_update(self, state: Dict[str, Any]):
        # The controller updates its belief when it receives new state info.
        self.current_level = state.get('level', self.current_level)

    def step(self, dt: float, **kwargs):
        # The core control logic.
        error = self.setpoint - self.current_level
        control_action = error * self.gain
        logging.info(f"Controller '{self.id}': Level={self.current_level:.2f}, Setpoint={self.setpoint}, Error={error:.2f}, Action={control_action:.2f}")
        self.message_bus.publish(self.command_topic, control_action, sender_id=self.id)


# --- 3. Main script to run the scenario ---
def run_agent_based_scenario():
    """Sets up and runs the agent-based simulation."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    message_bus = MessageBus()

    # Create the physical model that the BodyAgent will wrap
    tank_model = WaterTankModel(id="tank1", area=100.0, level=2.0)

    # Create the agents that form the system
    tank_agent = TankBodyAgent(id="tank1", message_bus=message_bus, model=tank_model)

    inflow_agent = InflowDisturbanceAgent(id="inflow_gen", message_bus=message_bus,
                                          target_topic="tank1.inflow.command", inflow_rate=5.0)

    control_agent = ProportionalControlAgent(id="pid_controller", message_bus=message_bus,
                                             state_topic="tank1.state", command_topic="tank1.outflow.command",
                                             setpoint=10.0, gain=0.5)

    # Initialize and run the simulation engine
    engine = SimulationEngine(
        mode=SimulationMode.SIL,
        agents=[tank_agent, inflow_agent, control_agent],
        message_bus=message_bus
    )
    engine.run(duration_seconds=20.0, time_step_seconds=1.0)
    logging.info("Scenario finished.")

if __name__ == "__main__":
    run_agent_based_scenario()
