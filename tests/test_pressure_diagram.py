"""侧压力分布数据与解析合力的一致性测试。"""

import unittest

from trenchlite import Groundwater, Load, SoilLayer
from trenchlite.solver import calculate_active_pressure


class PressureDiagramTests(unittest.TestCase):
    def test_dry_soil_diagram(self) -> None:
        soil = SoilLayer("砂土", thickness=5.0, gamma=18.0, c=0.0, phi=30.0)
        result = calculate_active_pressure(soil)
        points = result.pressure_diagram.points

        self.assertGreaterEqual(len(points), 20)
        self.assertEqual(points[0].depth, 0.0)
        self.assertEqual(points[0].pressure, 0.0)
        self.assertEqual(points[-1].depth, 5.0)
        self.assertTrue(all(left.depth < right.depth for left, right in zip(points, points[1:])))
        self.assertAlmostEqual(result.max_pressure, points[-1].pressure)
        self.assertAlmostEqual(result.pressure_diagram.total_force, result.total_force)
        self.assertAlmostEqual(result.pressure_diagram.application_depth, result.application_depth)

        integrated_force = sum(
            (left.pressure + right.pressure) / 2 * (right.depth - left.depth)
            for left, right in zip(points, points[1:])
        )
        self.assertLess(abs(integrated_force - result.total_force) / result.total_force, 0.05)

    def test_surcharge_and_water_diagram(self) -> None:
        soil = SoilLayer("砂土", thickness=5.0, gamma=18.0, c=0.0, phi=30.0)
        load = Load("均布超载", 20.0)
        groundwater = Groundwater(elevation=-3.1, name="地下水位")
        result = calculate_active_pressure(soil, load, groundwater)
        points = result.pressure_diagram.points

        self.assertAlmostEqual(points[0].pressure, result.Ka * load.value)
        self.assertTrue(any(abs(point.depth - 3.1) < 1e-12 for point in points))
        self.assertAlmostEqual(points[-1].pressure, result.max_pressure)
        integrated_force = sum(
            (left.pressure + right.pressure) / 2 * (right.depth - left.depth)
            for left, right in zip(points, points[1:])
        )
        self.assertAlmostEqual(integrated_force, result.total_force)


if __name__ == "__main__":
    unittest.main()
