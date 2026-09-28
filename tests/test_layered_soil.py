"""分层土剖面与 Rankine 主动压力测试。"""

import math
import unittest

from trenchlite import ExcavationProject, Groundwater, Load, SoilLayer, SoilProfile, Wall
from trenchlite.solver import calculate_active_pressure


class LayeredSoilTests(unittest.TestCase):
    def setUp(self) -> None:
        self.top = SoilLayer("填土", thickness=2.0, gamma=18.0, c=0.0, phi=20.0)
        self.bottom = SoilLayer("砂土", thickness=3.0, gamma=20.0, c=0.0, phi=30.0)
        self.profile = SoilProfile([self.top, self.bottom])

    def test_profile_layer_lookup_and_project(self) -> None:
        self.assertEqual(self.profile.total_depth, 5.0)
        self.assertIs(self.profile.get_layer_at_depth(1.0), self.top)
        self.assertIs(self.profile.get_layer_at_depth(2.0), self.bottom)
        self.assertIs(self.profile.get_layer_at_depth(5.0), self.bottom)
        with self.assertRaises(ValueError):
            self.profile.get_layer_at_depth(5.1)
        with self.assertRaises(ValueError):
            SoilProfile([])

        project = ExcavationProject("Layered Trench", 5.0, self.profile, Wall("钢板桩", 0.0, 0.0))
        self.assertIs(project.soils, self.profile)

    def test_interface_pressures_and_total_force(self) -> None:
        result = calculate_active_pressure(self.profile)
        points = result.pressure_diagram.points
        interface = [point for point in points if point.depth == 2.0]
        ka_top = (1 - math.sin(math.radians(20.0))) / (1 + math.sin(math.radians(20.0)))
        ka_bottom = 1 / 3

        self.assertEqual(len(interface), 2)
        self.assertAlmostEqual(interface[0].soil_pressure, ka_top * 18.0 * 2.0)
        self.assertAlmostEqual(interface[1].soil_pressure, ka_bottom * 18.0 * 2.0)
        self.assertAlmostEqual(result.pressure_diagram.points[-1].soil_pressure, ka_bottom * (18.0 * 2.0 + 20.0 * 3.0))
        self.assertAlmostEqual(result.soil_pressure, 36.0 * ka_top + 66.0)
        self.assertAlmostEqual(result.pressure_diagram.get_total_force(), result.total_force)

    def test_layered_surcharge_and_water_components(self) -> None:
        result = calculate_active_pressure(
            self.profile,
            Load("均布超载", 20.0),
            Groundwater(elevation=-3.0, name="地下水位"),
        )
        ka_top = (1 - math.sin(math.radians(20.0))) / (1 + math.sin(math.radians(20.0)))
        self.assertAlmostEqual(result.surcharge_pressure, 40.0 * ka_top + 20.0)
        self.assertAlmostEqual(result.water_pressure, 0.5 * 9.8 * 2.0**2)
        self.assertAlmostEqual(
            result.total_force,
            result.soil_pressure + result.surcharge_pressure + result.water_pressure,
        )


if __name__ == "__main__":
    unittest.main()
