import unittest
import sys
import os
import pandas as pd
import numpy as np

# Add the project root to the path to allow imports from chs_sdk
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from water_system_sdk.src.chs_sdk.preprocessing.interpolators import InverseDistanceWeightingInterpolator
from water_system_sdk.src.chs_sdk.preprocessing.structures import RainGauge

class TestPreprocessing(unittest.TestCase):

    def test_idw_interpolator(self):
        """
        Tests the InverseDistanceWeightingInterpolator for correct calculation.
        """
        # 1. Setup
        # Create two mock rain gauges
        gauge1_ts = pd.DataFrame({'rainfall': [10.0]}, index=[pd.to_datetime("2023-01-01 01:00:00")])
        gauge1 = RainGauge(id='g1', coords=(0, 0), time_series=gauge1_ts)

        gauge2_ts = pd.DataFrame({'rainfall': [20.0]}, index=[pd.to_datetime("2023-01-01 01:00:00")])
        gauge2 = RainGauge(id='g2', coords=(10, 0), time_series=gauge2_ts)

        rain_gauges = [gauge1, gauge2]

        # Define a target location exactly halfway between the two gauges
        target_locations = {"target1": (5, 0)}

        # 2. Instantiate the interpolator
        # With power=1, the weight is 1/distance.
        # The target is 5 units from g1 and 5 units from g2.
        # The weights should be equal (1/5 and 1/5).
        # The interpolated value should be the average: (10 * 0.5 + 20 * 0.5) = 15.0
        idw = InverseDistanceWeightingInterpolator(power=1)

        # 3. Run interpolation
        result_df = idw.interpolate(rain_gauges, target_locations)

        # 4. Assert
        self.assertIn("target1", result_df.columns)
        self.assertEqual(len(result_df), 1)
        interpolated_value = result_df.loc[pd.to_datetime("2023-01-01 01:00:00"), "target1"]
        self.assertAlmostEqual(interpolated_value, 15.0, places=7,
                               msg="IDW interpolation for equidistant point is incorrect.")

    def test_idw_interpolator_power2(self):
        """
        Tests the IDW interpolator with a different power parameter.
        """
        # 1. Setup
        gauge1_ts = pd.DataFrame({'rainfall': [10.0]}, index=[pd.to_datetime("2023-01-01 01:00:00")])
        gauge1 = RainGauge(id='g1', coords=(0, 0), time_series=gauge1_ts)

        gauge2_ts = pd.DataFrame({'rainfall': [30.0]}, index=[pd.to_datetime("2023-01-01 01:00:00")])
        gauge2 = RainGauge(id='g2', coords=(3, 0), time_series=gauge2_ts)

        rain_gauges = [gauge1, gauge2]

        # Target is 1 unit from g1 and 2 units from g2
        target_locations = {"target1": (1, 0)}

        # 2. Instantiate with power=2
        idw = InverseDistanceWeightingInterpolator(power=2)

        # 3. Manual calculation
        # dist1 = 1, dist2 = 2
        # w1 = 1 / 1^2 = 1
        # w2 = 1 / 2^2 = 0.25
        # total_weight = 1 + 0.25 = 1.25
        # value = (10 * 1 + 30 * 0.25) / 1.25 = (10 + 7.5) / 1.25 = 17.5 / 1.25 = 14.0
        expected_value = 14.0

        # 4. Run interpolation
        result_df = idw.interpolate(rain_gauges, target_locations)

        # 5. Assert
        interpolated_value = result_df.loc[pd.to_datetime("2023-01-01 01:00:00"), "target1"]
        self.assertAlmostEqual(interpolated_value, expected_value, places=7,
                               msg="IDW interpolation with power=2 is incorrect.")
