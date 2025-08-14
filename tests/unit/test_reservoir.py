import unittest
from water_system_simulator.modeling.storage_models import FirstOrderInertiaModel
from water_system_simulator.basic_tools.solvers import EulerIntegrator

class TestReservoir(unittest.TestCase):

    def test_mass_balance(self):
        """
        Tests the mass balance for the FirstOrderInertiaModel (Reservoir).
        Change in Storage = Inflow - Outflow
        """
        initial_storage = 1000.0  # m^3
        time_constant = 50.0      # T, where Outflow = Storage / T
        dt = 1.0                  # s
        inflow = 30.0             # m^3/s

        # Initial outflow
        initial_outflow = initial_storage / time_constant

        # Instantiate the model
        reservoir = FirstOrderInertiaModel(
            name="test_reservoir",
            initial_storage=initial_storage,
            time_constant=time_constant,
            solver_class=EulerIntegrator,
            dt=dt
        )

        # Run one step
        reservoir.input.inflow = inflow
        current_outflow = reservoir.step(t=0)

        # Get the new storage
        new_storage = reservoir.state.storage

        # Verify the mass balance
        # The ODE is dS/dt = I - O, where O = S/T
        # For an Euler step, S_new = S_old + (I_old - O_old) * dt
        # O_old is calculated from S_old
        expected_storage_change = (inflow - initial_outflow) * dt
        storage_change = new_storage - initial_storage

        # The new outflow is based on the new storage
        expected_new_outflow = new_storage / time_constant

        self.assertAlmostEqual(storage_change, expected_storage_change, places=5)
        self.assertAlmostEqual(current_outflow, expected_new_outflow, places=5)

if __name__ == '__main__':
    unittest.main()
