"""二维围护墙的离散节点。"""

from dataclasses import dataclass

from .spring import SoilSpring


@dataclass
class WallNode:
    """记录墙体节点编号、地表以下深度和水平位移。"""

    id: int
    depth: float
    displacement: float | None = None
    spring: SoilSpring | None = None
