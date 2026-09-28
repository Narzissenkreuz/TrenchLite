"""施工阶段序列的基础遍历接口。"""

from ..project import ExcavationProject
from ..result import StageResult


def analyze_stages(project: ExcavationProject) -> list[StageResult]:
    """按项目阶段顺序生成记录；当前不重新求解围护结构。"""

    stages = project.construction_sequence.stages if project.construction_sequence is not None else project.stages
    return [
        StageResult(stage_name=stage.name, excavation_depth=stage.excavation_depth, analysis_available=False)
        for stage in stages
    ]
