"""土压力计算方法选择与 Rankine 系数测试。"""

import unittest

from trenchlite import EarthPressureMethod, SoilLayer, SoilProfile
from trenchlite.solver import calculate_active_pressure, calculate_rankine_active_coefficient


class PressureMethodTests(unittest.TestCase):
    def test_default_matches_explicit_rankine(self) -> None:
        soil = SoilLayer("砂土", thickness=5.0, gamma=18.0, c=0.0, phi=30.0)
        self.assertEqual(
            calculate_active_pressure(soil),
            calculate_active_pressure(soil, method=EarthPressureMethod.RANKINE_ACTIVE),
        )
        profile = SoilProfile([soil])
        self.assertEqual(
            calculate_active_pressure(profile),
            calculate_active_pressure(profile, method=EarthPressureMethod.RANKINE_ACTIVE),
        )

    def test_rankine_active_coefficient(self) -> None:
        self.assertAlmostEqual(calculate_rankine_active_coefficient(30.0), 1 / 3)

    def test_coulomb_default_interface_matches_rankine(self) -> None:
        soil = SoilLayer("砂土", thickness=5.0, gamma=18.0, c=0.0, phi=30.0)
        rankine = calculate_active_pressure(soil)
        coulomb = calculate_active_pressure(soil, method=EarthPressureMethod.COULOMB_ACTIVE)
        self.assertAlmostEqual(coulomb.Ka, rankine.Ka)
        self.assertAlmostEqual(coulomb.total_force, rankine.total_force)


if __name__ == "__main__":
    unittest.main()
