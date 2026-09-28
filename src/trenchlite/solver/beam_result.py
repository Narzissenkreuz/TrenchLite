"""由离散墙体位移恢复简化梁单元内力。"""

from math import isfinite
from typing import Sequence

from ..model.beam import BeamElement2D
from ..result import BeamForceResult


def calculate_beam_forces(
    beam_element: BeamElement2D, node_displacements: Sequence[float]
) -> BeamForceResult:
    """以二阶差分曲率恢复单元中心弯矩及沿深度方向剪力。

    node_displacements 为整个等距墙体网格的节点位移，节点 id 与序列下标
    一致。顶部自由端弯矩取零，底部弯矩由相邻曲率线性外推；剪力为
    单元两端弯矩之差除以长度。该恢复方式与现有位移差分模型一致。
    """

    values = list(node_displacements)
    count = len(values)
    index = beam_element.node_i.id
    length = beam_element.length
    if count < 3 or index < 0 or index >= count - 1 or beam_element.node_j.id != index + 1:
        raise ValueError("梁单元节点 id 必须对应位移序列中的相邻节点")
    if not isfinite(length) or length <= 0 or not isfinite(beam_element.EI) or beam_element.EI <= 0:
        raise ValueError("梁单元长度和 EI 必须为正的有限数值")
    if any(not isfinite(value) for value in values):
        raise ValueError("节点位移必须为有限数值")

    def curvature(node_index: int) -> float:
        if node_index == 0:
            return 0.0
        if node_index == count - 1:
            return 2 * curvature(count - 2) - curvature(count - 3) if count > 3 else 2 * curvature(1)
        return (values[node_index - 1] - 2 * values[node_index] + values[node_index + 1]) / length**2

    moment_i = beam_element.EI * curvature(index)
    moment_j = beam_element.EI * curvature(index + 1)
    return BeamForceResult(moment=(moment_i + moment_j) / 2, shear=(moment_j - moment_i) / length)
