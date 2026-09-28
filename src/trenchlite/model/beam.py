"""二维围护墙的简化梁单元数据。"""

from dataclasses import dataclass

from .node import WallNode


@dataclass
class BeamElement2D:
    """连接两个墙节点并保存该段抗弯刚度。"""

    id: int
    node_i: WallNode
    node_j: WallNode
    EI: float

    @property
    def length(self) -> float:
        """返回单元沿深度方向的长度。"""

        return self.node_j.depth - self.node_i.depth
