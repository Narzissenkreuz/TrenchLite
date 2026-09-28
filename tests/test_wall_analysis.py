"""简化悬臂围护墙的剪力、弯矩测试。"""

import unittest

from trenchlite import PressureDiagram, PressurePoint, SoilLayer, SoilProfile, Wall, WallAnalysisResult, WallElement, WallModel, WallSection
from trenchlite.solver import analyze_wall, calculate_active_pressure


class WallAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        section = WallSection("试验截面", EI=1200.0, height=5.0)
        self.wall_model = WallModel(
            wall=Wall("钢板桩", EI=1200.0, W=50.0),
            elements=[WallElement(2.0, section), WallElement(3.0, section)],
        )

    def test_uniform_pressure_cantilever(self) -> None:
        points = [
            PressurePoint(depth=depth, soil_pressure=10.0, surcharge_pressure=0.0, water_pressure=0.0, total_pressure=10.0)
            for depth in (0.0, 2.5, 5.0)
        ]
        diagram = PressureDiagram(points=points, total_force=50.0, application_depth=2.5)
        result = analyze_wall(self.wall_model, diagram)

        self.assertIsInstance(result, WallAnalysisResult)
        self.assertEqual(result.depths, [0.0, 2.5, 5.0])
        self.assertEqual(len(result.moments), len(result.depths))
        self.assertEqual(len(result.shears), len(result.depths))
        self.assertEqual(len(result.displacements), len(result.depths))
        self.assertAlmostEqual(result.shears[-1], 50.0)
        self.assertAlmostEqual(result.moments[-1], 125.0)
        self.assertGreater(result.max_moment, 0.0)
        self.assertGreater(result.max_shear, 0.0)
        self.assertEqual(result.max_moment_depth, 5.0)
        self.assertEqual(result.max_shear_depth, 5.0)
        self.assertEqual(result.displacements, [0.0, 0.0, 0.0])

    def test_linearly_increasing_pressure(self) -> None:
        points = [
            PressurePoint(0.0, 0.0, 0.0, 0.0, 0.0),
            PressurePoint(5.0, 10.0, 0.0, 0.0, 10.0),
        ]
        diagram = PressureDiagram(points=points, total_force=25.0, application_depth=5.0 / 3)
        result = analyze_wall(self.wall_model, diagram)
        self.assertAlmostEqual(result.max_shear, 25.0)
        self.assertAlmostEqual(result.max_moment, 125.0 / 3.0)

    def test_layer_interface_pressure_jump(self) -> None:
        profile = SoilProfile(
            [
                SoilLayer("填土", 2.0, 18.0, 0.0, 20.0),
                SoilLayer("砂土", 3.0, 20.0, 0.0, 30.0),
            ]
        )
        pressure = calculate_active_pressure(profile)
        result = analyze_wall(self.wall_model, pressure.pressure_diagram)

        self.assertEqual(result.depths.count(2.0), 2)
        self.assertAlmostEqual(result.shears[-1], pressure.total_force)
        self.assertAlmostEqual(
            result.moments[-1],
            pressure.total_force * pressure.application_depth,
        )


if __name__ == "__main__":
    unittest.main()
