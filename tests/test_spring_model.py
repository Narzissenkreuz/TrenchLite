"""m 参数、土弹簧剖面和围护墙方法标记测试。"""

import unittest

from trenchlite import (
    PressureDiagram,
    PressurePoint,
    SoilLayer,
    SoilProfile,
    SoilSpring,
    SpringProfile,
    Wall,
    WallAnalysisMethod,
    WallElement,
    WallModel,
    WallSection,
)
from trenchlite.solver import analyze_wall, create_m_spring_profile


class SpringModelTests(unittest.TestCase):
    def test_soil_layer_stores_optional_m(self) -> None:
        old_style = SoilLayer("填土", 2.0, 18.0, 0.0, 20.0)
        with_m = SoilLayer("砂土", 3.0, 20.0, 0.0, 30.0, m=200.0)
        self.assertIsNone(old_style.m)
        self.assertEqual(with_m.m, 200.0)

    def test_spring_profile_creation(self) -> None:
        springs = [SoilSpring(depth=0.0, k=0.0), SoilSpring(depth=1.0, k=100.0)]
        profile = SpringProfile(springs=springs)
        self.assertEqual(profile.springs, springs)

    def test_spring_lookup_by_depth(self) -> None:
        first = SoilSpring(0.0, 0.0)
        second = SoilSpring(1.0, 100.0)
        profile = SpringProfile([first, second])
        self.assertIs(profile.get_spring_at_depth(0.5), first)
        self.assertIs(profile.get_spring_at_depth(1.0), second)
        with self.assertRaises(ValueError):
            profile.get_spring_at_depth(1.1)

    def test_layered_profile_uses_each_layer_m(self) -> None:
        soil_profile = SoilProfile(
            [
                SoilLayer("填土", 2.0, 18.0, 0.0, 20.0, m=100.0),
                SoilLayer("砂土", 3.0, 20.0, 0.0, 30.0, m=200.0),
            ]
        )
        spring_profile = create_m_spring_profile(soil_profile, wall_depth=5.0)
        self.assertGreaterEqual(len(spring_profile.springs), 21)
        self.assertEqual(spring_profile.get_spring_at_depth(1.0).k, 100.0)
        self.assertEqual(spring_profile.get_spring_at_depth(2.0).k, 400.0)
        self.assertEqual(spring_profile.get_spring_at_depth(4.0).k, 800.0)

    def test_cantilever_result_has_no_spring_profile(self) -> None:
        section = WallSection("试验截面", EI=1200.0, height=5.0)
        wall_model = WallModel(Wall("钢板桩", 1200.0, 50.0), [WallElement(5.0, section)])
        diagram = PressureDiagram(
            points=[
                PressurePoint(0.0, 10.0, 0.0, 0.0, 10.0),
                PressurePoint(5.0, 10.0, 0.0, 0.0, 10.0),
            ],
            total_force=50.0,
            application_depth=2.5,
        )
        result = analyze_wall(wall_model, diagram)
        self.assertIs(result.method, WallAnalysisMethod.CANTILEVER)
        self.assertIsNone(result.spring_profile)


if __name__ == "__main__":
    unittest.main()
