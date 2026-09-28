"""基础数据模型测试。"""

import unittest

from trenchlite import ExcavationProject, Groundwater, Section, SoilLayer, Strut, Wall


class DataModelTests(unittest.TestCase):
    def test_soil_layer_creation(self) -> None:
        soil = SoilLayer("粉质黏土", 5.0, 18.5, 15.0, 20.0)
        self.assertEqual(soil.name, "粉质黏土")
        self.assertEqual(soil.thickness, 5.0)
        self.assertEqual(soil.gamma, 18.5)
        self.assertEqual(soil.c, 15.0)
        self.assertEqual(soil.phi, 20.0)

    def test_wall_creation(self) -> None:
        wall = Wall("拉森IV型钢板桩", 100.0, 20.0)
        self.assertEqual(wall.name, "拉森IV型钢板桩")
        self.assertEqual(wall.EI, 100.0)
        self.assertEqual(wall.W, 20.0)

    def test_project_combines_models(self) -> None:
        soil = SoilLayer("粉质黏土", 5.0, 18.5, 15.0, 20.0)
        wall = Wall("拉森IV型钢板桩", 100.0, 20.0)
        strut = Strut("第一道支撑", -1.0, "609×16钢管")
        project = ExcavationProject("Test Trench", 5.0, [soil], wall, [strut])
        self.assertEqual(project.soils, [soil])
        self.assertIs(project.wall, wall)
        self.assertEqual(project.struts, [strut])
        self.assertEqual(project.loads, [])
        self.assertEqual(project.stages, [])
        self.assertIsNone(project.groundwater)
        self.assertEqual(project.sections, [])

    def test_groundwater_creation(self) -> None:
        groundwater = Groundwater(elevation=-2.0, name="地下水位")
        self.assertEqual(groundwater.name, "地下水位")
        self.assertEqual(groundwater.elevation, -2.0)

    def test_section_creation(self) -> None:
        section = Section(name="609×16钢管", area=1.0, inertia=2.0, modulus=3.0)
        self.assertEqual(section.area, 1.0)
        self.assertEqual(section.inertia, 2.0)
        self.assertEqual(section.modulus, 3.0)

    def test_project_with_groundwater(self) -> None:
        groundwater = Groundwater(elevation=-2.0, name="地下水位")
        soil = SoilLayer("粉质黏土", 5.0, 18.5, 15.0, 20.0)
        wall = Wall("拉森IV型钢板桩", 100.0, 20.0)
        project = ExcavationProject("Test Trench", 5.0, [soil], wall, groundwater=groundwater)
        self.assertIs(project.groundwater, groundwater)


if __name__ == "__main__":
    unittest.main()
