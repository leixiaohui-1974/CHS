import unittest
import numpy as np
from chs_sdk.agents.body_agents import RiverAgent, PipeAgent, HydropowerStationAgent
from chs_sdk.agents.message_bus import InMemoryMessageBus as MessageBus
from chs_sdk.agents.message import Message
from chs_sdk.agents.agent_status import AgentStatus

# A mock kernel for testing purposes
class MockKernel:
    def __init__(self, time_step=1.0):
        self.message_bus = MessageBus()
        self.current_time = 0
        self.time_step = time_step

class TestNewPhysicalModels(unittest.TestCase):

    def setUp(self):
        self.kernel = MockKernel()

    def test_river_agent_backwater_effect(self):
        """
        Tests if the RiverAgent can simulate a backwater curve caused by
        a high downstream water level.
        """
        nodes_data = [
            {'name': 'us_node', 'type': 'inflow', 'bed_elevation': 10.0, 'inflow': 150.0, 'head': 11.0},
            {'name': 'ds_node', 'type': 'level', 'bed_elevation': 9.0, 'level': 9.0, 'head': 9.0}
        ]
        reaches_data = [{
            'name': 'reach1', 'from_node': 'us_node', 'to_node': 'ds_node',
            'length': 10000, 'manning': 0.03,
            'shape': {'type': 'trapezoid', 'bottom_width': 50, 'side_slope': 0}
        }]

        boundary_topics = { "us_node": "boundary/inflow/us", "ds_node": "boundary/level/ds" }

        river_agent = RiverAgent(
            agent_id="river1", kernel=self.kernel, nodes_data=nodes_data,
            reaches_data=reaches_data, state_topic="state/river/river1",
            boundary_topics=boundary_topics
        )
        river_agent.setup()
        river_agent.status = AgentStatus.RUNNING

        self.kernel.message_bus.publish(Message(topic="boundary/inflow/us", payload={"value": 150.0}, sender_id="test"))
        downstream_water_level = 12.0
        self.kernel.message_bus.publish(Message(topic="boundary/level/ds", payload={"value": downstream_water_level}, sender_id="test"))

        for i in range(100):
            self.kernel.message_bus.dispatch()
            river_agent.execute(self.kernel.current_time)
            self.kernel.current_time += self.kernel.time_step

        final_state = river_agent.model.get_state()
        upstream_head = final_state['nodes']['us_node']['head']

        self.assertGreater(upstream_head, downstream_water_level, "Upstream head should be elevated by the backwater effect.")
        print(f"Backwater Test: Upstream Head = {upstream_head:.2f}m, Downstream Level = {downstream_water_level:.2f}m")

    def test_pipe_agent_flow_calculation(self):
        """
        Tests if the PipeAgent correctly calculates flow based on the Darcy-Weisbach head loss formula.
        """
        pipe_agent = PipeAgent(
            agent_id="pipe1", kernel=self.kernel, length=1000, diameter=1.0,
            friction_factor=0.02, inlet_pressure_topic="pressure/inlet",
            outlet_pressure_topic="pressure/outlet", state_topic="state/pipe/pipe1"
        )
        pipe_agent.setup()
        pipe_agent.status = AgentStatus.RUNNING

        inlet_pressure_head = 50.0
        outlet_pressure_head = 40.0
        self.kernel.message_bus.publish(Message(topic="pressure/inlet", payload={"pressure": inlet_pressure_head}, sender_id="test"))
        self.kernel.message_bus.publish(Message(topic="pressure/outlet", payload={"pressure": outlet_pressure_head}, sender_id="test"))

        # Run for more steps to allow inertia model to stabilize
        for _ in range(200):
            self.kernel.message_bus.dispatch()
            pipe_agent.execute(self.kernel.current_time)
            self.kernel.current_time += self.kernel.time_step

        state = pipe_agent.model.get_state()
        calculated_flow = state['flow']

        g = 9.81
        area = np.pi * (1.0**2) / 4
        head_loss = inlet_pressure_head - outlet_pressure_head
        expected_velocity = np.sqrt(head_loss * 2 * g * 1.0 / (0.02 * 1000))
        expected_flow = area * expected_velocity

        print(f"Pipe Flow Test: Calculated = {calculated_flow:.4f} m^3/s, Expected = {expected_flow:.4f} m^3/s")
        self.assertAlmostEqual(calculated_flow, expected_flow, places=2, msg="PipeAgent did not calculate the correct flow.")

    def test_hydropower_station_agent_power_calculation(self):
        """
        Tests if the HydropowerStationAgent correctly calculates flow and power.
        """
        station_agent = HydropowerStationAgent(
            agent_id="hydro1", kernel=self.kernel, max_flow_area=20.0,
            discharge_coeff=0.8, efficiency=0.9, upstream_topic="level/upstream",
            downstream_topic="level/downstream", vane_opening_topic="control/vane",
            state_topic="state/hydro/hydro1"
        )
        station_agent.setup()
        station_agent.status = AgentStatus.RUNNING

        upstream_level = 100.0
        downstream_level = 80.0
        vane_opening = 0.75

        self.kernel.message_bus.publish(Message(topic="level/upstream", payload={"level": upstream_level}, sender_id="test"))
        self.kernel.message_bus.publish(Message(topic="level/downstream", payload={"level": downstream_level}, sender_id="test"))
        self.kernel.message_bus.publish(Message(topic="control/vane", payload={"value": vane_opening}, sender_id="test"))

        self.kernel.message_bus.dispatch()
        station_agent.execute(self.kernel.current_time)

        state = station_agent.model.get_state()
        flow = state['flow']
        power = state['power']

        g = 9.81
        rho = 1000
        head = upstream_level - downstream_level
        effective_area = 20.0 * vane_opening
        expected_flow = 0.8 * effective_area * np.sqrt(2 * g * head)
        expected_power = 0.9 * rho * g * expected_flow * head

        print(f"Hydropower Test: Calculated Flow = {flow:.2f} m^3/s, Expected Flow = {expected_flow:.2f} m^3/s")
        print(f"Hydropower Test: Calculated Power = {power/1e6:.2f} MW, Expected Power = {expected_power/1e6:.2f} MW")

        self.assertAlmostEqual(flow, expected_flow, places=2, msg="Hydropower agent calculated incorrect flow.")
        self.assertAlmostEqual(power, expected_power, places=0, msg="Hydropower agent calculated incorrect power.")

if __name__ == '__main__':
    unittest.main()
