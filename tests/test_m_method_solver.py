"""基础线性梁-弹簧求解框架测试。"""

import math
import unittest

from trenchlite import (
    BeamElement2D,
    PressureDiagram,
    PressurePoint,
    SoilLayer,
    SoilProfile,
    Wall,
    WallAnalysisMethod,
    WallModel,
)
from trenchlite.solver import analyze_wall, analyze_wall_m_method, create_m_spring_profile


class MMethodSolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = WallModel(wall=Wall("试验墙", EI=1200.0, W=50.0))
        self.model.generate_mesh(height=5.0, element_count=10)
        soil = SoilProfile([SoilLayer("砂土", 5.0, 18.0, 0.0, 30.0, m=100.0)])
        self.springs = create_m_spring_profile(soil, wall_depth=5.0)
        self.diagram = PressureDiagram(
            points=[PressurePoint(z, 10.0, 0.0, 0.0, 10.0) for z in (0.0, 5.0)],
            total_force=50.0,
            application_depth=2.5,
        )

    def test_generate_mesh_connects_nodes_and_elements(self) -> None:
        self.assertEqual(len(self.model.nodes), 11)
        self.assertEqual(len(self.model.elements), 10)
        self.assertEqual(self.model.nodes[0].depth, 0.0)
        self.assertEqual(self.model.nodes[-1].depth, 5.0)
        self.assertIsInstance(self.model.elements[0], BeamElement2D)
        self.assertIs(self.model.elements[0].node_i, self.model.nodes[0])
        self.assertIs(self.model.elements[0].node_j, self.model.nodes[1])

    def test_m_method_returns_finite_displacements_and_node_springs(self) -> None:
        result = analyze_wall_m_method(self.model, self.diagram, self.springs)
        self.assertIs(result.method, WallAnalysisMethod.M_METHOD)
        self.assertIs(result.spring_profile, self.springs)
        self.assertEqual(result.status, "complete")
        self.assertFalse(result.incomplete)
        self.assertEqual(len(result.depths), 11)
        self.assertEqual(len(result.displacements), 11)
        self.assertTrue(all(math.isfinite(value) for value in result.displacements))
        self.assertGreater(max(result.displacements), 0.0)
        self.assertEqual(result.displacements[-2:], [0.0, 0.0])
        self.assertEqual(len(result.moments), 11)
        self.assertEqual(len(result.shears), 11)
        self.assertTrue(all(node.spring is not None for node in self.model.nodes))
        self.assertEqual(self.model.nodes[0].displacement, result.displacements[0])

    def test_stiffer_springs_reduce_max_displacement(self) -> None:
        soft = analyze_wall_m_method(self.model, self.diagram, self.springs)
        stiff_soil = SoilProfile([SoilLayer("砂土", 5.0, 18.0, 0.0, 30.0, m=1000.0)])
        stiff_springs = create_m_spring_profile(stiff_soil, wall_depth=5.0)
        stiff = analyze_wall_m_method(self.model, self.diagram, stiff_springs)
        self.assertLess(max(stiff.displacements), max(soft.displacements))

    def test_zero_pressure_has_zero_displacements_without_singularity(self) -> None:
        zero = PressureDiagram(
            points=[PressurePoint(z, 0.0, 0.0, 0.0, 0.0) for z in (0.0, 5.0)],
            total_force=0.0,
            application_depth=0.0,
        )
        result = analyze_wall_m_method(self.model, zero, self.springs)
        self.assertTrue(all(value == 0.0 for value in result.displacements))

    def test_cantilever_result_unchanged_on_generated_mesh(self) -> None:
        result = analyze_wall(self.model, self.diagram)
        self.assertIs(result.method, WallAnalysisMethod.CANTILEVER)
        self.assertIsNone(result.spring_profile)
        self.assertEqual(result.status, "complete")
        self.assertAlmostEqual(result.max_shear, 50.0)
        self.assertAlmostEqual(result.max_moment, 125.0)


if __name__ == "__main__":
    unittest.main()
