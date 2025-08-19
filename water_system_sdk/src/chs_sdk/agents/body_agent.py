from __future__ import annotations
from typing import Dict, Any, List
from .base import BaseAgent
from .message import StateUpdateMessage
from ..modeling.base_model import BaseModel
from scipy.optimize import fsolve
import numpy as np

class BodyAgent(BaseAgent):
    """
    The core of the new architecture, the "Agent Factory".

    This agent represents the complete, self-aware digital twin of a physical
    entity (e.g., a pump station, a stretch of canal). It not only simulates
    the physics but also has the intelligence to analyze its own behavior and
    automatically generate the necessary control and sensing agents for its
    operation.

    It has two primary modes:
    1. Live Digital Twin: When connected to real-world sensors, it uses data
       assimilation to stay synchronized with the physical asset.
    2. In-Loop Test Platform: When disconnected, it serves as a high-fidelity
       virtual environment for testing the agents it generates.
    """
    def __init__(self,
                 agent_id: str,
                 kernel: 'AgentKernel',
                 core_physics_model: BaseModel,
                 sensors: Dict[str, BaseModel],
                 actuators: Dict[str, BaseModel],
                 **kwargs):
        """
        Initializes the BodyAgent.

        Args:
            core_physics_model: The model representing the core physics of the entity.
            sensors: A dictionary of sensor models for perception.
            actuators: A dictionary of actuator models for action.
        """
        super().__init__(agent_id=agent_id, kernel=kernel, **kwargs)
        self.core_physics_model = core_physics_model
        self.sensors = sensors
        self.actuators = actuators

    def get_state_vector(self):
        """
        Returns the state vector of the core physics model.
        """
        if hasattr(self.core_physics_model, 'get_state_vector'):
            return self.core_physics_model.get_state_vector()
        # Fallback for models that might not have this method
        if hasattr(self.core_physics_model, 'state'):
             # This is a simple heuristic, might need to be more robust
            return np.array(list(self.core_physics_model.state.values()))
        return np.array([])


    def on_execute(self, current_time: float, time_step: float, **kwargs):
        """
        Drives the internal physics model and reports state.
        This is the main entry point when run by an AgentKernel.
        """
        if not self.core_physics_model:
            return

        # For now, we assume dynamic mode when run by kernel.
        # A more robust implementation might use the agent's FSM to manage modes.
        self.core_physics_model.step(dt=time_step, **kwargs)

        # Report state after execution
        self.report_state()

    def report_state(self):
        """
        Publishes the current state of the core physics model to the message bus.
        """
        if not hasattr(self.core_physics_model, 'get_state'):
            return

        current_state = self.core_physics_model.get_state()
        topic = f"state/update/{self.agent_id}"
        message = StateUpdateMessage(
            topic=topic,
            sender_id=self.agent_id,
            payload=current_state
        )
        self._publish(message.topic, message.payload)


    def step(self, dt: float, **kwargs):
        """
        Legacy step method for compatibility with SimulationManager.
        Delegates to on_execute.
        """
        self.on_execute(current_time=0, time_step=dt, **kwargs)

    def solve_steady_state(self, **kwargs):
        """
        Calculates the steady-state of the system using a root-finding algorithm.
        """
        if not hasattr(self.core_physics_model, 'get_state_vector') or \
           not hasattr(self.core_physics_model, 'get_derivatives'):
            print("ERROR: Steady-state solver requires the model to have 'get_state_vector' and 'get_derivatives' methods.")
            return

        initial_guess = self.core_physics_model.get_state_vector()

        # The function to find the root of: derivatives should be zero
        def objective_function(state_vector):
            # The model needs a way to set its internal state from this vector
            self.core_physics_model.set_state_from_vector(state_vector)
            # We want the derivatives to be zero at steady state
            return self.core_physics_model.get_derivatives(0, state_vector, **kwargs)

        try:
            steady_state_vector = fsolve(objective_function, initial_guess)
            # Once solved, update the model's state to this equilibrium point
            self.core_physics_model.set_state_from_vector(steady_state_vector)
            print(f"INFO: Steady-state found and set for {self.name}.")
        except Exception as e:
            print(f"ERROR: Failed to find steady-state for {self.name}: {e}")

    def characterize_dynamics(self) -> Dict[str, Any]:
        """
        Performs system identification on the core_physics_model to generate
        a high-fidelity "Model Bank" of its behavior.

        Returns:
            A dictionary representing the model bank, which can be used for
            designing controllers.
        """
        # Placeholder: In a real implementation, this would involve running
        # tests on the model (e.g., step responses) and fitting simplified
        # models (e.g., transfer functions, state-space models).
        print(f"INFO: Characterizing dynamics for {self.name}...")
        model_bank = {
            "type": "LinearTransferFunction",
            "parameters": {"num": [1.0], "den": [10.0, 1.0]},
            "description": "A simplified first-order model identified from the core physics."
        }
        print(f"INFO: Dynamics characterized. Model bank generated.")
        return model_bank

    def auto_generate_control_agents(self, control_type: str = "PID") -> Dict[str, Any]:
        """
        Uses the model bank to automatically generate a configuration for a
        suitable controller.

        Args:
            control_type: The desired type of controller (e.g., "PID", "MPC").

        Returns:
            A configuration dictionary for the new control agent.
        """
        # Placeholder: This would use control theory (e.g., Ziegler-Nichols for PID)
        # or optimization to design a controller based on the identified model.
        print(f"INFO: Auto-generating '{control_type}' controller for {self.name}...")
        if control_type.upper() == "PID":
            pid_config = {
                "name": f"{self.name}_PID_Controller",
                "type": "PIDController",
                "properties": {
                    "kp": 1.5, "ki": 0.05, "kd": 0.2,
                    "setpoint_path": f"{self.name}.input.setpoint" # Example path
                }
            }
            print("INFO: PID controller configuration generated.")
            return pid_config
        else:
            raise NotImplementedError(f"Control type '{control_type}' not supported for auto-generation.")

    def assemble_test_scenario(self, control_agent_config: Dict[str, Any], disturbance_agents_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assembles a complete simulation configuration for an in-loop test.

        This method takes the parent BodyAgent (self), a generated
        control agent, and a set of disturbances, and packages them into a
        valid configuration dictionary that can be run by the SimulationManager.

        Args:
            control_agent_config: The configuration for the control agent.
            disturbance_agents_config: A list of configurations for disturbance agents.

        Returns:
            A complete simulation configuration dictionary.
        """
        print("INFO: Assembling Software-in-the-Loop test scenario...")
        # The body agent itself is a component
        body_agent_name = self.name
        components = {
            body_agent_name: {
                "type": "BodyAgent",
                # The properties will be the same as this instance
            }
        }
        # Add the controller
        components[control_agent_config["name"]] = control_agent_config
        # Add disturbances
        for dist_config in disturbance_agents_config:
            components[dist_config["name"]] = dist_config

        # Create a basic execution order
        execution_order = [
            # In a real scenario, this would be more complex, defining
            # the precise flow of information from sensors to controllers
            # and back to actuators.
            control_agent_config["name"],
            body_agent_name
        ]

        final_config = {
            "components": components,
            "execution_order": execution_order,
            "simulation_params": {"total_time": 100, "dt": 1},
            "logger_config": [f"{body_agent_name}.sensors.level_sensor.output"]
        }
        print("INFO: Test scenario assembled.")
        return final_config
