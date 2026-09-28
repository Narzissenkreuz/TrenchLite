"""计算结果基础数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .model.spring import SpringProfile

if TYPE_CHECKING:
    from .solver.wall_method import WallAnalysisMethod


def _default_wall_method() -> WallAnalysisMethod:
    """延迟读取默认方法，避免结果模型和求解器循环导入。"""

    from .solver.wall_method import WallAnalysisMethod

    return WallAnalysisMethod.CANTILEVER


@dataclass
class CalculationResult:
    """以名称和值字典保存计算结果。"""

    name: str
    values: dict[str, object]


@dataclass
class PressurePoint:
    """记录地表以下深度及土、超载、水和总侧压力，单位为 m、kPa。"""

    depth: float
    soil_pressure: float
    surcharge_pressure: float
    water_pressure: float
    total_pressure: float

    @property
    def pressure(self) -> float:
        """兼容旧接口，返回该深度的总侧压力。"""

        return self.total_pressure


@dataclass
class PressureDiagram:
    """保存侧压力离散点、总合力及合力距坑底的作用点。"""

    points: list[PressurePoint]
    total_force: float
    application_depth: float

    def get_total_force(self) -> float:
        """用梯形积分求总侧压力合力，单位为 kN/m。"""

        return sum(
            (left.total_pressure + right.total_pressure) * (right.depth - left.depth) / 2
            for left, right in zip(self.points, self.points[1:])
        )

    def get_component_force(self) -> dict[str, float]:
        """用梯形积分返回土、超载和水压力合力，单位为 kN/m。"""

        forces = {"soil_pressure": 0.0, "surcharge_pressure": 0.0, "water_pressure": 0.0}
        for left, right in zip(self.points, self.points[1:]):
            width = (right.depth - left.depth) / 2
            forces["soil_pressure"] += (left.soil_pressure + right.soil_pressure) * width
            forces["surcharge_pressure"] += (left.surcharge_pressure + right.surcharge_pressure) * width
            forces["water_pressure"] += (left.water_pressure + right.water_pressure) * width
        return forces


@dataclass
class ActivePressureResult(CalculationResult):
    """保存侧压力各分量及合力；作用点距坑底的距离以 m 计。"""

    values: dict[str, object] = field(init=False)
    Ka: float
    max_pressure: float
    total_force: float
    application_depth: float
    soil_pressure: float = 0.0
    surcharge_pressure: float = 0.0
    water_pressure: float = 0.0
    pressure_diagram: PressureDiagram = field(
        default_factory=lambda: PressureDiagram(points=[], total_force=0.0, application_depth=0.0)
    )
    method: str = "Rankine"

    def __post_init__(self) -> None:
        """同步通用结果接口与具名结果字段。"""

        self.values = {
            "Ka": self.Ka,
            "max_pressure": self.max_pressure,
            "total_force": self.total_force,
            "application_depth": self.application_depth,
            "soil_pressure": self.soil_pressure,
            "surcharge_pressure": self.surcharge_pressure,
            "water_pressure": self.water_pressure,
            "pressure_diagram": self.pressure_diagram,
            "method": self.method,
        }


@dataclass
class WallAnalysisResult:
    """保存围护墙沿深度的位移、弯矩和剪力结果。"""

    depths: list[float]
    moments: list[float]
    shears: list[float]
    displacements: list[float]
    max_moment: float = 0.0
    max_shear: float = 0.0
    max_moment_depth: float = 0.0
    max_shear_depth: float = 0.0
    method: WallAnalysisMethod = field(default_factory=_default_wall_method)
    spring_profile: SpringProfile | None = None
    status: str = "complete"
    incomplete: bool = False
    moment_diagram: list[tuple[float, float]] = field(default_factory=list)
    shear_diagram: list[tuple[float, float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """在未显式提供时由深度和内力数组构造可绘图数据。"""

        if not self.moment_diagram and self.moments:
            self.moment_diagram = list(zip(self.depths, self.moments))
        if not self.shear_diagram and self.shears:
            self.shear_diagram = list(zip(self.depths, self.shears))


@dataclass
class BeamForceResult:
    """保存梁单元中心处的弯矩和剪力，单位为 kN·m/m、kN/m。"""

    moment: float
    shear: float


@dataclass
class SectionCheckResult:
    """保存线弹性弯曲应力、允许应力和利用率。"""

    max_stress: float
    allowable_stress: float
    utilization: float


@dataclass
class StageResult:
    """记录已遍历的施工阶段及其是否具有结构分析结果。"""

    stage_name: str
    excavation_depth: float
    analysis_available: bool
