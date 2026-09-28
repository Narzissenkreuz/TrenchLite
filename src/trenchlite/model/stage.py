"""施工阶段及其顺序数据模型。"""

from dataclasses import dataclass, field
from math import isfinite

from ..structure import Strut


@dataclass
class ExcavationStage:
    """记录一个开挖状态；installed_struts 仅保存已安装支撑的数据。"""

    name: str
    excavation_depth: float
    installed_struts: list[Strut] = field(default_factory=list)
    description: str = ""

    def __post_init__(self) -> None:
        """确保初始状态和分步开挖深度有效。"""

        if not isfinite(self.excavation_depth) or self.excavation_depth < 0:
            raise ValueError("施工阶段开挖深度必须为非负有限数值")


@dataclass
class ConstructionSequence:
    """按录入顺序保存初始、开挖及支撑安装阶段。"""

    stages: list[ExcavationStage] = field(default_factory=list)

    def add_stage(self, stage: ExcavationStage) -> None:
        """按施工顺序追加一个阶段。"""

        if not isinstance(stage, ExcavationStage):
            raise TypeError("stage 必须为 ExcavationStage")
        if self.stages and stage.excavation_depth < self.stages[-1].excavation_depth:
            raise ValueError("新增阶段的开挖深度不能小于上一阶段")
        self.stages.append(stage)

    def get_final_stage(self) -> ExcavationStage:
        """返回最后一个阶段；空序列抛出明确异常。"""

        if not self.stages:
            raise ValueError("施工阶段序列为空")
        return self.stages[-1]
