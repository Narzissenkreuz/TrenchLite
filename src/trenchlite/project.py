"""工程数据模型。"""

from dataclasses import dataclass, field

from .load import Load
from .model import ConstructionSequence, SoilProfile
from .section import Section
from .soil import SoilLayer
from .stage import ExcavationStage
from .structure import Strut, Wall
from .water import Groundwater


@dataclass
class ExcavationProject:
    """组合沟槽工程的土层、支护、荷载和施工阶段。"""

    name: str
    depth: float
    soils: list[SoilLayer] | SoilProfile
    wall: Wall
    struts: list[Strut] = field(default_factory=list)
    loads: list[Load] = field(default_factory=list)
    stages: list[ExcavationStage] = field(default_factory=list)
    groundwater: Groundwater | None = None
    sections: list[Section] = field(default_factory=list)
    construction_sequence: ConstructionSequence | None = None
