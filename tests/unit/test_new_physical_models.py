import unittest
import numpy as np
import sys
import os

# Ensure the source directory is in the Python path
# This is a common pattern for running tests in a package structure
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../water_system_sdk/src')))

# Now we can import the modules from the simulator
from water_system_simulator.modeling.actuator_models import ActuatorBase
from water_system_simulator.modeling.instrument_models import SensorBase
from water_system_simulator.modeling.valve_models import GenericValve
from water_system_simulator.modeling.control_structure_models import SluiceGate
from water_system_simulator.modeling.pump_models import CentrifugalPump, PositiveDisplacementPump
from water_system_simulator.modeling.station_models import PumpingStation, AuxiliarySystem
from water_system_simulator.modeling.storage_models import NonlinearTank
from water_system_simulator.modeling.pipeline_model import PipelineModel
from water_system_simulator.modeling.channel_models import ChannelModel


# A dummy base model for testing components that need it
from water_system_simulator.modeling.base_model import BaseModel

class TestNewPhysicalModels(unittest.TestCase):

    def test_valve_model(self):
        """Tests the flow calculation of a GenericValve."""
        # A simple linear Cv curve: Cv = 100 * opening
        valve = GenericValve(cv_curve=lambda x: 100 * x, initial_opening=0.5, name="TestValve")
        # Update with pressures and time step
        valve.step(upstream_pressure=10, downstream_pressure=6, dt=1.0)
        # Expected flow: Q = Cv * sqrt(dP) = (100 * 0.5) * sqrt(10 - 6) = 50 * 2 = 100
        self.assertAlmostEqual(valve.flow, 100.0, delta=0.1)

    def test_gate_model(self):
        """Tests the SluiceGate model under free-flow conditions."""
        gate = SluiceGate(gate_width=2, discharge_coeff=0.6, initial_opening=1.0, name="TestGate")
        gate.step(upstream_level=5, downstream_level=0.5, dt=1.0)
        # Expected flow Q = C_d * b * a * sqrt(2 * g * h1)
        expected_flow = 0.6 * 2 * 1.0 * np.sqrt(2 * 9.81 * 5)
        self.assertAlmostEqual(gate.flow, expected_flow, delta=0.1)

    def test_pump_model(self):
        """Tests the CentrifugalPump model's operating point calculation."""
        # Define a simple quadratic HQ curve: H(Q) = 100 - 0.1*Q^2
        hq_curve = lambda q: 100 - 0.1 * q**2
        # Define a simple efficiency curve
        eff_q_curve = lambda q: 0.8
        pump = CentrifugalPump(hq_curve=hq_curve, eff_q_curve=eff_q_curve, initial_speed=1.0, name="TestPump")

        # System head is a constant 80m. Find Q where pump head = system head.
        # 100 - 0.1*Q^2 = 80  => 20 = 0.1*Q^2 => Q^2 = 200 => Q = sqrt(200) ~= 14.142
        pump.step(system_head=80, dt=1.0)
        # The simple solver in the model isn't perfect, so we use a looser delta
        self.assertAlmostEqual(pump.flow, 14.14, delta=0.2)

    def test_station_model(self):
        """Tests the PumpingStation's aggregation of flow and power."""
        # Cannot instantiate PumpBase directly, use a concrete implementation
        pump1 = PositiveDisplacementPump(rated_flow=1.0, name="P1")
        pump2 = PositiveDisplacementPump(rated_flow=1.0, name="P2")
        aux = AuxiliarySystem(base_power_draw=100, operational_power_draw=500)
        station = PumpingStation(pumps=[pump1, pump2], auxiliary_system=aux, name="TestStation")

        # Set pump speeds
        pump1.set_speed(1.0)
        pump2.set_speed(0.5)

        station.step(system_head=50, dt=1.0)
        # Total flow should be 1.0 + 0.5 = 1.5
        self.assertEqual(station.total_flow, 1.5)
        # Since pumps are on, aux power should be base + operational
        self.assertEqual(station.aux_system.power, 600)

    def test_nonlinear_tank_model(self):
        """Tests the NonlinearTank with a lookup table."""
        # level-volume curve: [[levels], [volumes]]
        curve = np.array([
            [0., 1., 2., 3., 4.], # levels (m)
            [0., 100., 300., 600., 1000.]  # volumes (m^3)
        ])
        tank = NonlinearTank(level_to_volume=curve, initial_level=2.0, name="TestNonlinearTank")
        self.assertAlmostEqual(tank.volume, 300)

        # inflow=50, outflow=10 for 10 seconds -> net inflow volume = 400 m^3
        tank.input.inflow = 50
        tank.input.release_outflow = 10
        tank.step(dt=10.0)

        # Expected volume = 300 (initial) + 400 (net inflow) = 700
        self.assertAlmostEqual(tank.volume, 700.0)
        # From curve, 700 m^3 corresponds to level 3.25
        self.assertAlmostEqual(tank.get_level(700.0), 3.25)
        self.assertAlmostEqual(tank.level, 3.25)

    def test_pipeline_quality_model(self):
        """Tests the water quality advection in the PipelineModel."""
        pipe = PipelineModel(length=100, diameter=1, quality_steps=10, initial_concentration=0.0, name="TestPipeQuality")
        pipe.flow = pipe.area * 10 # Set velocity to 10 m/s

        # Cell length is 10m. It takes 1s for water to cross one cell.
        # Run for one step. The upstream concentration should now be in the first element of the deque.
        pipe.update_quality(upstream_concentration=100.0, dt=1.0)

        self.assertAlmostEqual(pipe.concentrations[0], 100.0)
        # The outlet is the *last* element of the deque (what's flowing out now)
        self.assertAlmostEqual(pipe.get_outlet_concentration(), 0.0)

        # Run for 9 more seconds. The pulse should have just reached the outlet.
        for _ in range(9):
            # After the first pulse, the upstream concentration goes back to 0
            pipe.update_quality(upstream_concentration=0.0, dt=1.0)
        self.assertAlmostEqual(pipe.get_outlet_concentration(), 100.0)

    def test_channel_model_instantiation(self):
        """Smoke test for the ChannelModel."""
        channel = ChannelModel(
            length=1000,
            num_cells=10,
            cross_section={'shape_type': 'trapezoid', 'bottom_width': 10, 'side_slope': 2},
            manning_n=0.03,
            bed_slope=0.001,
            name="TestChannel"
        )
        self.assertIsNotNone(channel)
        # Check that initial flow is non-zero if depth is non-zero
        self.assertGreater(channel.flows[-1], 0)

        # Check that depth in the first cell increases with a large upstream inflow
        initial_depth_cell_0 = channel.depths[0]
        channel.step(dt=1.0, upstream_flow=500) # A large inflow compared to initial equilibrium
        self.assertGreater(channel.depths[0], initial_depth_cell_0)


if __name__ == '__main__':
    unittest.main()
