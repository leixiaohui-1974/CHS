import numpy as np
from .base_agent import BaseAgent
from .message import Message, MeasurementPayload
from water_system_simulator.modeling.storage_models import ReservoirModel
from water_system_simulator.modeling.control_structure_models import GateModel, PumpStationModel, HydropowerStationModel
from water_system_simulator.modeling.pipeline_model import PipelineModel
from water_system_simulator.modeling.hydrodynamics.routing_models import MuskingumModel

try:
    # Use a full path import to be robust
    from chs_sdk.components.control.kalman_filter import KalmanFilter
except (ImportError, ModuleNotFoundError):
    # This allows the module to be used even if the KalmanFilter component is not available.
    KalmanFilter = None


class TankAgent(BaseAgent):
    """
    An agent that encapsulates a water tank (reservoir) model, with optional
    Kalman Filter for data assimilation.
    """
    def __init__(self, agent_id, kernel, area, initial_level, max_level=20.0, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)
        self.model = ReservoirModel(area=area, initial_level=initial_level, max_level=max_level)

        if self.config.get("enable_kalman_filter", False) and KalmanFilter is not None:
            kf_config = self.config.get("kalman_filter", {})

            # Default matrices for a 1D system (e.g., water level)
            F = np.array(kf_config.get("F", [[1.0]]))
            H = np.array(kf_config.get("H", [[1.0]]))
            Q = np.array(kf_config.get("Q", [[0.001]])) # Process noise
            R = np.array(kf_config.get("R", [[0.1]]))   # Measurement noise

            # Use initial_level for the initial state estimate, accessing it correctly
            initial_state_estimate = [self.model.state.level]
            x0 = np.array(kf_config.get("x0", initial_state_estimate))
            P0 = np.array(kf_config.get("P0", [[1.0]])) # Initial uncertainty

            self.filter = KalmanFilter(F=F, H=H, Q=Q, R=R, x0=x0, P0=P0)
            print(f"TankAgent {self.agent_id} initialized with Kalman Filter.")

    def setup(self):
        """
        Subscribe to the necessary topics for control and data assimilation.
        """
        for topic in self.config.get("subscribes_to", []):
            self.kernel.message_bus.subscribe(self, topic)
        if self.filter:
            measurement_topic = f"measurement/level/{self.agent_id}"
            self.kernel.message_bus.subscribe(self, measurement_topic)
            print(f"TankAgent {self.agent_id} subscribed to {measurement_topic}")

    def execute(self, current_time: float):
        """
        Runs one step of the reservoir simulation, applying data assimilation if enabled.
        """
        time_step = self.kernel.time_step if hasattr(self.kernel, 'time_step') else 1.0
        publishes_to = self.config.get("publishes_to", f"tank/{self.agent_id}/state")


        # Run the physical model step first to get its own prediction
        self.model.step(time_step)

        if self.filter:
            # The filter's state is x_{k-1|k-1}. Predict to get x_k|k-1.
            self.filter.predict()

            # The 'update' step happens asynchronously in on_message when a measurement arrives.
            # After update, the filter state is x_k|k (the best estimate).

            # Now, correct the model's state with the filter's best estimate.
            corrected_level = self.filter.get_state()[0]
            self.model.state.level = corrected_level

            # Publish the corrected, high-fidelity state
            state_to_publish = self.model.get_state()
            self._publish(publishes_to, state_to_publish)
        else:
            # Original behavior: publish the raw model state
            self._publish(publishes_to, self.model.get_state())

    def on_message(self, message: Message):
        """
        Handles incoming messages for control inputs and measurement data.
        """
        topic = message.topic
        payload = message.payload

        if self.filter and topic.startswith("measurement/"):
            if isinstance(payload, dict):
                measurement_value = payload.get('value')
                if measurement_value is not None:
                    self._assimilate(measurement_value)

        elif topic.startswith("data.inflow"):
            self.model.input.inflow = payload.get("value", 0)
        elif topic.startswith("state/valve/"):
            self.model.input.release_outflow = payload.get("flow", 0)
        elif topic.startswith("demand/"):
            self.model.input.demand_outflow = payload.get("value", 0)


class GateAgent(BaseAgent):
    """
    An agent that encapsulates a gate model.
    """
    def __init__(self, agent_id, kernel, num_gates, gate_width, discharge_coeff,
                 upstream_topic, downstream_topic, opening_topic, state_topic, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)
        self.model = GateModel(
            num_gates=num_gates,
            gate_width=gate_width,
            discharge_coeff=discharge_coeff
        )
        self.upstream_topic = upstream_topic
        self.downstream_topic = downstream_topic
        self.opening_topic = opening_topic
        self.state_topic = state_topic

        self.upstream_level = 0.0
        self.downstream_level = 0.0
        self.gate_opening = 0.0

    def setup(self):
        """
        Subscribe to the necessary topics for gate operation.
        """
        self.kernel.message_bus.subscribe(self, self.upstream_topic)
        self.kernel.message_bus.subscribe(self, self.downstream_topic)
        self.kernel.message_bus.subscribe(self, self.opening_topic)

    def execute(self, current_time: float):
        """
        Runs one step of the gate simulation.
        """
        self.model.step(self.upstream_level, self.downstream_level, self.gate_opening)
        self._publish(self.state_topic, self.model.get_state())

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the gate's inputs.
        """
        if message.topic == self.upstream_topic:
            self.upstream_level = message.payload.get("level", message.payload.get("output", 0.0))
        elif message.topic == self.downstream_topic:
            self.downstream_level = message.payload.get("level", message.payload.get("output", 0.0))
        elif message.topic == self.opening_topic:
            self.gate_opening = message.payload.get("value", 0.0)


class ValveAgent(BaseAgent):
    """
    A simplified agent that encapsulates a valve.
    Its flow is determined by a flow coefficient (cv) and an opening percentage.
    """
    def __init__(self, agent_id, kernel, cv, subscribes_to, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)
        self.cv = cv
        self.opening = 0.0  # 0.0 to 1.0
        self.flow = 0.0
        # The agent subscribes to a topic that provides the opening command.
        self.opening_topic = subscribes_to[0] if isinstance(subscribes_to, list) else subscribes_to

    def setup(self):
        """
        Subscribe to the necessary topics for valve operation.
        """
        self.kernel.message_bus.subscribe(self, self.opening_topic)

    def execute(self, current_time: float):
        """
        Runs one step of the valve simulation.
        This is a simplified model: flow = cv * opening.
        A more realistic model would include pressure difference.
        """
        self.flow = self.cv * self.opening
        # Note: A valve doesn't have a state to publish on its own.
        # It's an actuator. Its effect is on other agents.
        # However, we can publish its internal state for monitoring.
        self._publish(f"state/valve/{self.agent_id}", {"opening": self.opening, "flow": self.flow})

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the valve's opening.
        """
        if message.topic == self.opening_topic:
            self.opening = message.payload.get("value", 0.0)


from .fsm import State, StateMachine
import time


# --- Pump States ---

class PumpBaseState(State):
    @property
    def agent(self) -> 'PumpAgent':
        return self._agent

    def on_message(self, message: Message):
        """
        Common message handling for all pump states.
        """
        if message.topic == self.agent.inlet_pressure_topic:
            self.agent.inlet_pressure = message.payload.get("value", 0.0)
        elif message.topic == self.agent.outlet_pressure_topic:
            self.agent.outlet_pressure = message.payload.get("value", 0.0)
        elif message.topic == "cmd.pump.stop":
            self.agent.transition_to('PumpStoppedState')
        elif message.topic == "cmd.pump.fault":
            self.agent.transition_to('PumpFaultState')


class PumpStoppedState(PumpBaseState):
    def on_enter(self):
        self.agent.num_pumps_on = 0
        self.agent.model.num_pumps_on = 0
        print(f"{self.agent.agent_id} entered StoppedState.")

    def execute(self, current_time: float):
        # In stopped state, the pump does nothing, just reports its state.
        self.agent.model.step(self.agent.inlet_pressure, self.agent.outlet_pressure, 0)
        self.agent._publish(self.agent.state_topic, {**self.agent.model.get_state(), "status": "stopped"})

    def on_message(self, message: Message):
        super().on_message(message)
        if message.topic == "cmd.pump.start":
            self.agent.transition_to('PumpStartingState')


class PumpStartingState(PumpBaseState):
    def on_enter(self):
        self.start_time = self.agent.kernel.current_time
        self.duration = 5  # Simulate a 5-second startup time
        print(f"{self.agent.agent_id} entered StartingState.")

    def execute(self, current_time: float):
        elapsed_time = current_time - self.start_time
        if elapsed_time >= self.duration:
            self.agent.transition_to('PumpRunningState')
            return

        # Simulate gradual startup (e.g., flow increases linearly)
        # For now, we just wait and then switch to running.
        # A more complex model could be implemented here.
        self.agent.num_pumps_on = self.agent.target_num_pumps
        self.agent.model.step(self.agent.inlet_pressure, self.agent.outlet_pressure, self.agent.num_pumps_on)
        self.agent._publish(self.agent.state_topic, {
            **self.agent.model.get_state(),
            "status": "starting",
            "progress": elapsed_time / self.duration
        })

    def on_message(self, message: Message):
        super().on_message(message)
        # Cannot change number of pumps while starting
        if message.topic == self.agent.num_pumps_on_topic:
            pass # Ignore


class PumpRunningState(PumpBaseState):
    def on_enter(self):
        # Set the number of pumps to the target, in case it was changed
        # while in another state.
        self.agent.num_pumps_on = self.agent.target_num_pumps
        self.agent.model.num_pumps_on = self.agent.target_num_pumps
        print(f"{self.agent.agent_id} entered RunningState.")

    def execute(self, current_time: float):
        self.agent.model.step(self.agent.inlet_pressure, self.agent.outlet_pressure, self.agent.num_pumps_on)
        self.agent._publish(self.agent.state_topic, {**self.agent.model.get_state(), "status": "running"})

    def on_message(self, message: Message):
        super().on_message(message)
        if message.topic == self.agent.num_pumps_on_topic:
            new_pump_count = message.payload.get("value", 1)
            if new_pump_count != self.agent.num_pumps_on:
                self.agent.target_num_pumps = new_pump_count
                # Potentially transition to a "Changing" state, but for now, just update
                self.agent.num_pumps_on = new_pump_count
                self.agent.model.num_pumps_on = new_pump_count


class PumpFaultState(PumpBaseState):
    def on_enter(self):
        self.agent.num_pumps_on = 0
        self.agent.model.num_pumps_on = 0
        print(f"{self.agent.agent_id} entered FaultState.")

    def execute(self, current_time: float):
        self.agent.model.step(self.agent.inlet_pressure, self.agent.outlet_pressure, 0)
        self.agent._publish(self.agent.state_topic, {**self.agent.model.get_state(), "status": "fault"})

    def on_message(self, message: Message):
        super().on_message(message)
        # Only a 'reset' command can move it out of fault state
        if message.topic == "cmd.pump.reset":
            self.agent.transition_to('PumpStoppedState')


class PumpAgent(BaseAgent):
    """
    An agent that encapsulates a pump station model, now driven by a state machine.
    """
    def __init__(self, agent_id, kernel, num_pumps_total, curve_coeffs,
                 inlet_pressure_topic, outlet_pressure_topic, num_pumps_on_topic, state_topic,
                 initial_num_pumps_on=0, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)
        self.model = PumpStationModel(
            num_pumps_total=num_pumps_total,
            curve_coeffs=curve_coeffs,
            initial_num_pumps_on=initial_num_pumps_on
        )
        self.inlet_pressure_topic = inlet_pressure_topic
        self.outlet_pressure_topic = outlet_pressure_topic
        self.num_pumps_on_topic = num_pumps_on_topic
        self.state_topic = state_topic

        self.inlet_pressure = 0.0
        self.outlet_pressure = 0.0
        self.num_pumps_on = initial_num_pumps_on
        self.target_num_pumps = initial_num_pumps_on if initial_num_pumps_on > 0 else 1

        # State Machine Initialization
        stopped_state = PumpStoppedState(self)
        self.state_machine = StateMachine(stopped_state)
        self.state_machine.add_state(PumpStartingState(self))
        self.state_machine.add_state(PumpRunningState(self))
        self.state_machine.add_state(PumpFaultState(self))

    def setup(self):
        """
        Subscribe to the necessary topics for pump operation.
        """
        self.kernel.message_bus.subscribe(self, self.inlet_pressure_topic)
        self.kernel.message_bus.subscribe(self, self.outlet_pressure_topic)
        self.kernel.message_bus.subscribe(self, self.num_pumps_on_topic)
        # Subscribe to command topics
        self.kernel.message_bus.subscribe(self, "cmd.pump.start")
        self.kernel.message_bus.subscribe(self, "cmd.pump.stop")
        self.kernel.message_bus.subscribe(self, "cmd.pump.fault")
        self.kernel.message_bus.subscribe(self, "cmd.pump.reset")


class HydropowerStationAgent(BaseAgent):
    """
    An agent that encapsulates a hydropower station model.
    It is a composite agent that coordinates internal models.
    """
    def __init__(self, agent_id, kernel, max_flow_area, discharge_coeff, efficiency,
                 upstream_topic, downstream_topic, vane_opening_topic, state_topic,
                 release_topic=None, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)
        self.model = HydropowerStationModel(
            max_flow_area=max_flow_area,
            discharge_coeff=discharge_coeff,
            efficiency=efficiency
        )
        self.upstream_topic = upstream_topic
        self.downstream_topic = downstream_topic
        self.vane_opening_topic = vane_opening_topic
        self.state_topic = state_topic
        self.release_topic = release_topic

        self.upstream_level = 0.0
        self.downstream_level = 0.0
        self.vane_opening = 0.0

    def setup(self):
        """
        Subscribe to the necessary topics for hydropower station operation.
        """
        self.kernel.message_bus.subscribe(self, self.upstream_topic)
        self.kernel.message_bus.subscribe(self, self.downstream_topic)
        self.kernel.message_bus.subscribe(self, self.vane_opening_topic)

    def execute(self, current_time: float):
        """
        Runs one step of the hydropower station simulation.
        Publishes its full state and also the release flow if a topic is provided.
        """
        self.model.step(self.upstream_level, self.downstream_level, self.vane_opening)
        state = self.model.get_state()
        self._publish(self.state_topic, state)

        # Also publish the release flow to a dedicated topic if configured
        if self.release_topic:
            self._publish(self.release_topic, {"value": state.get("flow", 0.0)})

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the station's inputs.
        """
        if message.topic == self.upstream_topic:
            self.upstream_level = message.payload.get("level", 0.0)
        elif message.topic == self.downstream_topic:
            # Allow for different payload structures
            self.downstream_level = message.payload.get("level", message.payload.get("value", 0.0))
        elif message.topic == self.vane_opening_topic:
            self.vane_opening = message.payload.get("value", 0.0)


class PipeAgent(BaseAgent):
    """
    An agent that encapsulates a pressurized pipe model.
    """
    def __init__(self, agent_id, kernel, length, diameter, friction_factor,
                 inlet_pressure_topic, outlet_pressure_topic, state_topic, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)
        self.model = PipelineModel(
            length=length,
            diameter=diameter,
            friction_factor=friction_factor
        )
        self.inlet_pressure_topic = inlet_pressure_topic
        self.outlet_pressure_topic = outlet_pressure_topic
        self.state_topic = state_topic

        self.inlet_pressure = 0.0
        self.outlet_pressure = 0.0

    def setup(self):
        """
        Subscribe to the necessary topics for pipe simulation.
        """
        self.kernel.message_bus.subscribe(self, self.inlet_pressure_topic)
        self.kernel.message_bus.subscribe(self, self.outlet_pressure_topic)

    def execute(self, current_time: float):
        """
        Runs one step of the pipe simulation.
        """
        time_step = self.kernel.time_step if hasattr(self.kernel, 'time_step') else 1.0
        self.model.step(self.inlet_pressure, self.outlet_pressure, time_step)
        self._publish(self.state_topic, self.model.get_state())

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the pipe's boundary conditions.
        """
        if message.topic == self.inlet_pressure_topic:
            self.inlet_pressure = message.payload.get("pressure", 0.0)
        elif message.topic == self.outlet_pressure_topic:
            self.outlet_pressure = message.payload.get("pressure", 0.0)


class ChannelAgent(BaseAgent):
    """
    An agent that represents a river or channel reach, using a routing model.
    """
    def __init__(self, agent_id, kernel, K, x, initial_outflow,
                 inflow_topic, state_topic, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)
        time_step = self.kernel.time_step if hasattr(self.kernel, 'time_step') else 1.0
        self.model = MuskingumModel(
            K=K,
            x=x,
            dt=time_step,
            initial_outflow=initial_outflow
        )
        self.inflow_topic = inflow_topic
        self.state_topic = state_topic
        self.current_inflow = initial_outflow

    def setup(self):
        """
        Subscribe to the necessary topics for channel simulation.
        """
        self.kernel.message_bus.subscribe(self, self.inflow_topic)

    def execute(self, current_time: float):
        """
        Runs one step of the channel routing simulation.
        """
        self.model.step(self.current_inflow)
        self._publish(self.state_topic, self.model.get_state())

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the channel's inflow.
        """
        if message.topic == self.inflow_topic:
            # The inflow can come from various sources (e.g., gate, another channel)
            # We look for 'flow' or 'output' keys in the payload.
            self.current_inflow = message.payload.get("flow", message.payload.get("output", 0.0))
