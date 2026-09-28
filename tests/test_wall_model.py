"""二维围护墙数据模型和分析接口测试。"""

import unittest

from trenchlite import PressureDiagram, Wall, WallAnalysisResult, WallElement, WallModel, WallSection
from trenchlite.solver import analyze_wall


class WallModelTests(unittest.TestCase):
    def test_wall_section_creation(self) -> None:
        section = WallSection(name="试验截面", EI=1200.0, height=5.0)
        self.assertEqual(section.name, "试验截面")
        self.assertEqual(section.EI, 1200.0)
        self.assertEqual(section.height, 5.0)

    def test_wall_element_uses_section(self) -> None:
        section = WallSection("试验截面", 1200.0, 5.0)
        element = WallElement(length=2.5, section=section)
        self.assertEqual(element.length, 2.5)
        self.assertIs(element.section, section)

    def test_wall_model_holds_multiple_elements(self) -> None:
        wall = Wall("钢板桩", EI=1200.0, W=50.0)
        section = WallSection("试验截面", EI=1200.0, height=5.0)
        elements = [WallElement(2.0, section), WallElement(3.0, section)]
        model = WallModel(wall=wall, elements=elements)
        self.assertIs(model.wall, wall)
        self.assertEqual(model.elements, elements)

    def test_wall_analysis_result_structure(self) -> None:
        result = WallAnalysisResult(
            depths=[0.0, 5.0],
            moments=[0.0, 0.0],
            shears=[0.0, 0.0],
            displacements=[0.0, 0.0],
        )
        self.assertEqual(result.depths, [0.0, 5.0])
        self.assertEqual(result.moments, [0.0, 0.0])
        self.assertEqual(result.shears, [0.0, 0.0])
        self.assertEqual(result.displacements, [0.0, 0.0])

    def test_analyze_wall_interface_exists(self) -> None:
        self.assertTrue(callable(analyze_wall))


if __name__ == "__main__":
    unittest.main()
