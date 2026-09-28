"""施工阶段模型与阶段遍历接口测试。"""

import unittest

from trenchlite import ConstructionSequence, ExcavationProject, ExcavationStage, SoilLayer, StageResult, Strut, Wall
from trenchlite.model.stage import ExcavationStage as ModelStage
from trenchlite.solver import analyze_stages


class StageModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.soil = SoilLayer("砂土", 5.0, 18.0, 0.0, 30.0)
        self.wall = Wall("试验墙", EI=1200.0, W=0.01)

    def test_create_initial_and_excavation_stages(self) -> None:
        initial = ExcavationStage("初始状态", 0.0)
        excavation = ExcavationStage("开挖 2 m", 2.0, description="第一步开挖")
        self.assertIs(ExcavationStage, ModelStage)
        self.assertEqual(initial.excavation_depth, 0.0)
        self.assertEqual(excavation.description, "第一步开挖")
        self.assertEqual(excavation.installed_struts, [])

    def test_sequence_preserves_stage_order_and_support_data(self) -> None:
        strut = Strut("第一道支撑", -1.0, "609×16钢管")
        stages = ConstructionSequence()
        stages.add_stage(ExcavationStage("初始状态", 0.0))
        stages.add_stage(ExcavationStage("开挖 2 m", 2.0))
        stages.add_stage(ExcavationStage("安装支撑", 2.0, installed_struts=[strut]))
        stages.add_stage(ExcavationStage("开挖 5 m", 5.0, installed_struts=[strut]))
        self.assertEqual([stage.name for stage in stages.stages], ["初始状态", "开挖 2 m", "安装支撑", "开挖 5 m"])
        self.assertIs(stages.stages[2].installed_struts[0], strut)

    def test_final_stage_and_empty_sequence(self) -> None:
        sequence = ConstructionSequence()
        with self.assertRaises(ValueError):
            sequence.get_final_stage()
        final = ExcavationStage("开挖 5 m", 5.0)
        sequence.add_stage(final)
        self.assertIs(sequence.get_final_stage(), final)

    def test_project_holds_sequence_without_changing_legacy_stages(self) -> None:
        legacy = ExcavationStage("旧阶段", 1.0)
        sequence = ConstructionSequence([ExcavationStage("初始状态", 0.0), ExcavationStage("开挖 5 m", 5.0)])
        project = ExcavationProject("Test", 5.0, [self.soil], self.wall, stages=[legacy], construction_sequence=sequence)
        self.assertIs(project.construction_sequence, sequence)
        self.assertEqual(project.stages, [legacy])

    def test_analyze_stages_only_traverses_without_solving(self) -> None:
        sequence = ConstructionSequence([ExcavationStage("初始状态", 0.0), ExcavationStage("开挖 2 m", 2.0), ExcavationStage("开挖 5 m", 5.0)])
        project = ExcavationProject("Test", 5.0, [self.soil], self.wall, construction_sequence=sequence)
        results = analyze_stages(project)
        self.assertEqual([result.stage_name for result in results], ["初始状态", "开挖 2 m", "开挖 5 m"])
        self.assertEqual([result.excavation_depth for result in results], [0.0, 2.0, 5.0])
        self.assertTrue(all(isinstance(result, StageResult) for result in results))
        self.assertTrue(all(not result.analysis_available for result in results))

    def test_legacy_project_stages_still_traverse(self) -> None:
        project = ExcavationProject("Test", 5.0, [self.soil], self.wall, stages=[ExcavationStage("开挖 2 m", 2.0)])
        self.assertEqual(analyze_stages(project), [StageResult("开挖 2 m", 2.0, False)])


if __name__ == "__main__":
    unittest.main()
