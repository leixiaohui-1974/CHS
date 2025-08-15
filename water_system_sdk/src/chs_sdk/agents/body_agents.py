from .base_agent import BaseAgent
from .message import Message
from water_system_sdk.src.water_system_simulator.modeling.storage_models import ReservoirModel
from water_system_sdk.src.water_system_simulator.modeling.control_structure_models import GateModel, PumpStationModel


class TankAgent(BaseAgent):
    """
    An agent that encapsulates a water tank (reservoir) model.
    """
    def __init__(self, agent_id, kernel, area, initial_level, max_level=20.0, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)
        self.model = ReservoirModel(area=area, initial_level=initial_level, max_level=max_level)

    def setup(self):
        """
        Subscribe to the necessary topics.
        """
        self.kernel.message_bus.subscribe(f"tank/{self.agent_id}/inflow", self)
        self.kernel.message_bus.subscribe(f"tank/{self.agent_id}/release_outflow", self)
        self.kernel.message_bus.subscribe(f"tank/{self.agent_id}/demand_outflow", self)

    def execute(self, current_time: float):
        """
        Runs one step of the reservoir simulation.
        """
        time_step = self.kernel.time_step if hasattr(self.kernel, 'time_step') else 1.0
        self.model.step(time_step)
        self._publish(f"tank/{self.agent_id}/state", self.model.get_state())

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the tank's inputs.
        """
        if message.topic == f"tank/{self.agent_id}/inflow":
            self.model.input.inflow = message.payload.get("value", 0)
        elif message.topic == f"tank/{self.agent_id}/release_outflow":
            self.model.input.release_outflow = message.payload.get("value", 0)
        elif message.topic == f"tank/{self.agent_id}/demand_outflow":
            self.model.input.demand_outflow = message.payload.get("value", 0)


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
        self.kernel.message_bus.subscribe(self.upstream_topic, self)
        self.kernel.message_bus.subscribe(self.downstream_topic, self)
        self.kernel.message_bus.subscribe(self.opening_topic, self)

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
    An agent that encapsulates a valve, modeled using the GateModel logic.
    It operates on its own topics for inputs and outputs.
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
        Subscribe to the necessary topics for valve operation.
        """
        self.kernel.message_bus.subscribe(self.upstream_topic, self)
        self.kernel.message_bus.subscribe(self.downstream_topic, self)
        self.kernel.message_bus.subscribe(self.opening_topic, self)

    def execute(self, current_time: float):
        """
        Runs one step of the valve simulation.
        """
        self.model.step(self.upstream_level, self.downstream_level, self.gate_opening)
        self._publish(self.state_topic, self.model.get_state())

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the valve's inputs.
        """
        if message.topic == self.upstream_topic:
            self.upstream_level = message.payload.get("level", message.payload.get("output", 0.0))
        elif message.topic == self.downstream_topic:
            self.downstream_level = message.payload.get("level", message.payload.get("output", 0.0))
        elif message.topic == self.opening_topic:
            self.gate_opening = message.payload.get("value", 0.0)


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
        self.kernel.message_bus.subscribe(self.inlet_pressure_topic, self)
        self.kernel.message_bus.subscribe(self.outlet_pressure_topic, self)
        self.kernel.message_bus.subscribe(self.num_pumps_on_topic, self)
        # Subscribe to command topics
        self.kernel.message_bus.subscribe("cmd.pump.start", self)
        self.kernel.message_bus.subscribe("cmd.pump.stop", self)
        self.kernel.message_bus.subscribe("cmd.pump.fault", self)
        self.kernel.message_bus.subscribe("cmd.pump.reset", self)
