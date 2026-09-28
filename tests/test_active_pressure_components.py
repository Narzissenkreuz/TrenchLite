"""主动土压力各分量及合力测试。"""

import unittest

from trenchlite import Groundwater, Load, SoilLayer
from trenchlite.solver import calculate_active_pressure


class ActivePressureComponentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.soil = SoilLayer("砂土", thickness=5.0, gamma=18.0, c=0.0, phi=30.0)
        self.load = Load("地面均布超载", 20.0)
        self.groundwater = Groundwater(elevation=-3.0, name="地下水位")

    def test_soil_only_matches_phase_1_0(self) -> None:
        result = calculate_active_pressure(self.soil)
        self.assertAlmostEqual(result.Ka, 1 / 3)
        self.assertAlmostEqual(result.max_pressure, 30.0)
        self.assertAlmostEqual(result.soil_pressure, 75.0)
        self.assertEqual(result.surcharge_pressure, 0.0)
        self.assertEqual(result.water_pressure, 0.0)
        self.assertAlmostEqual(result.total_force, 75.0)
        self.assertAlmostEqual(result.application_depth, 5.0 / 3.0)

    def test_uniform_surcharge(self) -> None:
        result = calculate_active_pressure(self.soil, load=self.load)
        self.assertAlmostEqual(result.surcharge_pressure, (1 / 3) * 20.0 * 5.0)
        self.assertEqual(result.water_pressure, 0.0)

    def test_groundwater(self) -> None:
        result = calculate_active_pressure(self.soil, groundwater=self.groundwater)
        self.assertAlmostEqual(result.water_pressure, 0.5 * 9.8 * 2.0**2)
        self.assertEqual(result.surcharge_pressure, 0.0)

    def test_combined_force_and_application_point(self) -> None:
        result = calculate_active_pressure(self.soil, self.load, self.groundwater)
        expected_moment = 75.0 * 5.0 / 3.0 + result.surcharge_pressure * 5.0 / 2.0 + result.water_pressure * 2.0 / 3.0
        self.assertAlmostEqual(
            result.total_force,
            result.soil_pressure + result.surcharge_pressure + result.water_pressure,
        )
        self.assertAlmostEqual(result.application_depth, expected_moment / result.total_force)
        self.assertAlmostEqual(result.max_pressure, 30.0 + (1 / 3) * 20.0 + 9.8 * 2.0)
        self.assertEqual(result.values["water_pressure"], result.water_pressure)


if __name__ == "__main__":
    unittest.main()
