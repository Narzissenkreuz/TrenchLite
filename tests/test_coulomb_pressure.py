"""Coulomb 主动土压力系数与方法分发测试。"""

import math
import unittest

from trenchlite import EarthPressureMethod, SoilLayer, WallInterface
from trenchlite.solver import (
    calculate_active_pressure,
    calculate_coulomb_active_coefficient,
    calculate_rankine_active_coefficient,
)


class CoulombPressureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.soil = SoilLayer("砂土", thickness=5.0, gamma=18.0, c=0.0, phi=30.0)

    def test_zero_interface_angles_match_rankine(self) -> None:
        coulomb_ka = calculate_coulomb_active_coefficient(30.0, 0.0, 0.0, 0.0)
        rankine_ka = calculate_rankine_active_coefficient(30.0)
        self.assertLess(abs(coulomb_ka - 1 / 3), 0.001)
        self.assertAlmostEqual(coulomb_ka, rankine_ka)

        result = calculate_active_pressure(
            self.soil,
            method=EarthPressureMethod.COULOMB_ACTIVE,
            wall_interface=WallInterface(),
        )
        self.assertEqual(result.method, "Coulomb")
        self.assertEqual(result.values["method"], "Coulomb")
        self.assertAlmostEqual(result.Ka, rankine_ka)

    def test_wall_friction_changes_coefficient_and_force(self) -> None:
        interface = WallInterface(delta=15.0)
        result = calculate_active_pressure(
            self.soil,
            method=EarthPressureMethod.COULOMB_ACTIVE,
            wall_interface=interface,
        )
        rankine = calculate_active_pressure(self.soil)
        self.assertTrue(math.isfinite(result.Ka))
        self.assertGreater(result.Ka, 0.0)
        self.assertNotAlmostEqual(result.Ka, rankine.Ka)
        self.assertNotAlmostEqual(result.total_force, rankine.total_force)

    def test_wall_and_ground_angles(self) -> None:
        ka = calculate_coulomb_active_coefficient(30.0, 10.0, 5.0, 10.0)
        self.assertTrue(math.isfinite(ka))
        self.assertGreater(ka, 0.0)


if __name__ == "__main__":
    unittest.main()
