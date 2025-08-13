import unittest
import numpy as np
import meshio
import os

from water_system_simulator.modeling.two_dimensional_hydrodynamic_model import TwoDimensionalHydrodynamicModel

class Test2DHydroModel(unittest.TestCase):

    def setUp(self):
        """Set up a simple mesh and model for testing."""
        self.mesh_file = "test_slope.msh"

        points = np.array([
            [0.0, 0.0, 0.0],
            [10.0, 0.0, 0.0],
            [0.0, 10.0, 0.0],
            [10.0, 10.0, 0.0]
        ])
        cells = [("triangle", np.array([[0, 1, 2], [1, 3, 2]]))]
        mesh = meshio.Mesh(points, cells)
        meshio.write(self.mesh_file, mesh)

        # To define a bed elevation that slopes with x, we first need the cell centers.
        # We can get them by creating a temporary mesh object.
        temp_mesh = TwoDimensionalHydrodynamicModel(mesh_file=self.mesh_file).mesh
        cell_centers = temp_mesh.cell_centers

        self.bed_elevation = -0.1 * cell_centers[:, 0]

        self.model = TwoDimensionalHydrodynamicModel(
            mesh_file=self.mesh_file,
            initial_h=1.0,
            bed_elevation=self.bed_elevation,
            manning_n=0.0, # No friction for this test
            cfl=0.4
        )

    def tearDown(self):
        """Clean up the created mesh file."""
        if os.path.exists(self.mesh_file):
            os.remove(self.mesh_file)

    def test_water_flows_downhill(self):
        """
        Tests the fundamental behavior: water should move from a higher WSE
        to a lower WSE, driven by gravity.
        """
        h_initial = self.model.data_manager.h.copy()

        for _ in range(30):
            self.model.step(dt=0, t=0)

        h_final = self.model.data_manager.h

        # Cell 0 is upstream (higher bed elevation), Cell 1 is downstream.
        # Water should move from Cell 0 to Cell 1.
        self.assertLess(h_final[0], h_initial[0], "Water depth in upstream cell [0] should decrease.")
        self.assertGreater(h_final[1], h_initial[1], "Water depth in downstream cell [1] should increase.")

        initial_volume = np.sum(h_initial * self.model.mesh.cell_areas)
        final_volume = np.sum(h_final * self.model.mesh.cell_areas)
        self.assertAlmostEqual(initial_volume, final_volume, places=3, msg="Total water volume should be conserved.")

if __name__ == '__main__':
    unittest.main()
