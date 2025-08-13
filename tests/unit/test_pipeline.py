import unittest
import numpy as np
from water_system_simulator.modeling.pipeline_model import PipelineModel

class TestPipeline(unittest.TestCase):

    def test_headloss_and_flow_calculation(self):
        """
        Tests the headloss calculation's effect on flow in the PipelineModel.
        It verifies that the flow is updated correctly according to the
        pressure difference and Darcy-Weisbach headloss.
        """
        length = 1000.0  # m
        diameter = 0.5   # m
        friction_factor = 0.02
        initial_flow = 1.0  # m^3/s
        dt = 1.0          # s
        g = 9.81

        inlet_pressure = 100.0 # m
        outlet_pressure = 90.0 # m

        # Instantiate the model
        pipeline = PipelineModel(
            name="test_pipeline",
            length=length,
            diameter=diameter,
            friction_factor=friction_factor,
            initial_flow=initial_flow
        )

        # --- Calculate expected values ---
        area = np.pi * (diameter ** 2) / 4
        initial_velocity = initial_flow / area

        # Expected head loss due to friction
        head_loss_friction = (friction_factor * (length / diameter) *
                              (initial_velocity**2 / (2 * g)))

        # Expected net head and acceleration
        delta_h_pressure = inlet_pressure - outlet_pressure
        net_head = delta_h_pressure - head_loss_friction
        expected_acceleration = (g * net_head) / length

        # Expected new velocity and flow
        expected_new_velocity = initial_velocity + expected_acceleration * dt
        expected_new_flow = expected_new_velocity * area

        # --- Run one step in the model ---
        pipeline.step(
            inlet_pressure=inlet_pressure,
            outlet_pressure=outlet_pressure,
            dt=dt
        )
        calculated_new_flow = pipeline.flow

        # --- Assert ---
        self.assertAlmostEqual(calculated_new_flow, expected_new_flow, places=5)

if __name__ == '__main__':
    unittest.main()
