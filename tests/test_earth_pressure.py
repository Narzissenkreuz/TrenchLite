"""Rankine 主动土压力计算测试。"""

import unittest

from trenchlite import ActivePressureResult, CalculationResult, SoilLayer
from trenchlite.solver import calculate_active_pressure


class ActivePressureTests(unittest.TestCase):
    def test_rankine_cohesionless_soil(self) -> None:
        soil = SoilLayer(name="砂土", thickness=5.0, gamma=18.0, c=0.0, phi=30.0)
        result = calculate_active_pressure(soil)

        self.assertIsInstance(result, ActivePressureResult)
        self.assertIsInstance(result, CalculationResult)
        self.assertLess(abs(result.Ka - 1 / 3), 0.001)
        self.assertAlmostEqual(result.max_pressure, result.Ka * 18.0 * 5.0)
        self.assertAlmostEqual(result.total_force, 0.5 * result.max_pressure * 5.0)
        self.assertAlmostEqual(result.application_depth, 5.0 / 3.0)
        self.assertEqual(result.values["Ka"], result.Ka)

    def test_rejects_cohesive_soil(self) -> None:
        soil = SoilLayer(name="粉质黏土", thickness=5.0, gamma=18.0, c=15.0, phi=30.0)
        with self.assertRaises(ValueError):
            calculate_active_pressure(soil)


if __name__ == "__main__":
    unittest.main()
