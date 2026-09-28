"""m 法内力恢复及线弹性截面验算测试。"""

import math
import unittest

from trenchlite import (
    PressureDiagram,
    PressurePoint,
    SoilSpring,
    SpringProfile,
    Wall,
    WallModel,
    WallSection,
)
from trenchlite.solver import analyze_wall_m_method, calculate_beam_forces, check_bending_stress


class MMethodResultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = WallModel(wall=Wall("试验墙", EI=1200.0, W=0.01))
        self.model.generate_mesh(height=5.0, element_count=20)
        self.diagram = PressureDiagram(
            points=[PressurePoint(z, 10.0, 0.0, 0.0, 10.0) for z in (0.0, 5.0)],
            total_force=50.0,
            application_depth=2.5,
        )
        self.springs = SpringProfile([SoilSpring(0.0, 0.0), SoilSpring(5.0, 0.0)])

    def test_m_method_outputs_displacements_and_complete_result(self) -> None:
        result = analyze_wall_m_method(self.model, self.diagram, self.springs)
        self.assertFalse(result.incomplete)
        self.assertEqual(result.status, "complete")
        self.assertEqual(len(result.displacements), len(self.model.nodes))
        self.assertGreater(max(result.displacements), 0.0)

    def test_recovers_moment_and_diagram(self) -> None:
        result = analyze_wall_m_method(self.model, self.diagram, self.springs)
        self.assertEqual(len(result.moments), len(result.depths))
        self.assertEqual(result.moment_diagram, list(zip(result.depths, result.moments)))
        self.assertTrue(all(math.isfinite(value) for value in result.moments))
        self.assertGreater(result.max_moment, 0.0)

    def test_recovers_shear_and_diagram(self) -> None:
        result = analyze_wall_m_method(self.model, self.diagram, self.springs)
        self.assertEqual(len(result.shears), len(result.depths))
        self.assertEqual(result.shear_diagram, list(zip(result.depths, result.shears)))
        self.assertTrue(all(math.isfinite(value) for value in result.shears))
        self.assertGreater(result.max_shear, 0.0)

    def test_uniform_load_trend_and_beam_force_recovery(self) -> None:
        result = analyze_wall_m_method(self.model, self.diagram, self.springs)
        self.assertAlmostEqual(result.max_moment, 125.0, delta=5.0)
        self.assertAlmostEqual(result.max_shear, 50.0, delta=5.0)
        self.assertEqual(result.max_moment_depth, 5.0)
        self.assertGreater(result.moments[-1], result.moments[len(result.moments) // 2])

        # 三次位移场的二阶差分曲率及其梯度可精确恢复单元中心内力。
        cubic_displacements = [node.depth**3 for node in self.model.nodes]
        element = self.model.elements[5]
        forces = calculate_beam_forces(element, cubic_displacements)
        center = (element.node_i.depth + element.node_j.depth) / 2
        self.assertAlmostEqual(forces.moment, element.EI * 6 * center)
        self.assertAlmostEqual(forces.shear, element.EI * 6)

    def test_bending_stress_uses_absolute_moment_over_w(self) -> None:
        section = WallSection("试验截面", EI=1200.0, height=5.0, section_modulus=0.01, material_strength=200000.0)
        check = check_bending_stress(-100.0, section)
        self.assertEqual(section.W, 0.01)
        self.assertAlmostEqual(check.max_stress, 10000.0)
        self.assertAlmostEqual(check.allowable_stress, 200000.0)
        self.assertAlmostEqual(check.utilization, 0.05)
        section_by_w = WallSection("W 别名", EI=1200.0, height=5.0, W=0.01, material_strength=200000.0)
        self.assertAlmostEqual(check_bending_stress(100.0, section_by_w).max_stress, 10000.0)
        with self.assertRaises(ValueError):
            check_bending_stress(100.0, WallSection("无 W", 1200.0, 5.0))


if __name__ == "__main__":
    unittest.main()
