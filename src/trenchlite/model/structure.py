"""二维围护结构的组合模型。"""

from dataclasses import dataclass, field
from math import isfinite

from ..structure import Wall
from .beam import BeamElement2D
from .node import WallNode
from .wall import WallElement


@dataclass
class WallModel:
    """保存既有 Wall 对象和组成二维墙体的梁单元。"""

    wall: Wall
    elements: list[WallElement | BeamElement2D] = field(default_factory=list)
    nodes: list[WallNode] = field(default_factory=list)

    def generate_mesh(self, height: float, element_count: int) -> None:
        """按墙高均匀生成节点和梁单元，替换当前离散单元。"""

        if not isfinite(height) or height <= 0:
            raise ValueError("墙高必须为正的有限数值")
        if isinstance(element_count, bool) or not isinstance(element_count, int) or element_count < 2:
            raise ValueError("单元数量必须为至少 2 的整数")
        if not isfinite(self.wall.EI) or self.wall.EI <= 0:
            raise ValueError("墙体 EI 必须为正的有限数值")

        self.nodes = [WallNode(id=index, depth=height * index / element_count) for index in range(element_count + 1)]
        self.elements = [
            BeamElement2D(id=index, node_i=self.nodes[index], node_j=self.nodes[index + 1], EI=self.wall.EI)
            for index in range(element_count)
        ]
