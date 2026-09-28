"""简化悬臂围护墙受侧压力分析。"""

from math import isclose, isfinite

import numpy as np

from ..model.beam import BeamElement2D
from ..model.spring import SpringProfile
from ..model.structure import WallModel
from ..result import PressureDiagram, WallAnalysisResult
from .beam_result import calculate_beam_forces
from .wall_method import WallAnalysisMethod


def analyze_wall(wall_model: WallModel, pressure_diagram: PressureDiagram) -> WallAnalysisResult:
    """积分求顶部自由、底部固定的墙体剪力与弯矩。

    墙高为各 WallElement.length 之和，深度自墙顶向下。压力点之间按线性
    分布处理；正侧压力产生正剪力和正弯矩。输入压力为 kPa 时，结果剪力
    为 kN/m、弯矩为 kN·m/m。当前不使用 EI，也不计算位移、支撑或土反力。
    """

    if not wall_model.elements:
        raise ValueError("围护墙模型至少需要一个梁单元")
    lengths = [element.length for element in wall_model.elements]
    if any(not isfinite(length) or length <= 0 for length in lengths):
        raise ValueError("梁单元长度必须为正的有限数值")
    height = sum(lengths)

    points = pressure_diagram.points
    if len(points) < 2:
        raise ValueError("压力分布至少需要两个点")
    depths = [point.depth for point in points]
    if not isclose(depths[0], 0.0, abs_tol=1e-9) or not isclose(
        depths[-1], height, rel_tol=1e-9, abs_tol=1e-9
    ):
        raise ValueError("压力分布必须从墙顶 0 m 覆盖至墙底")
    if any(not isfinite(point.depth) or not isfinite(point.total_pressure) for point in points):
        raise ValueError("压力点深度和总压力必须为有限数值")
    if any(right.depth < left.depth for left, right in zip(points, points[1:])):
        raise ValueError("压力点深度必须从墙顶向墙底排列")

    shears = [0.0]
    moments = [0.0]
    for upper, lower in zip(points, points[1:]):
        length = lower.depth - upper.depth
        # 线性分布压力在本段的等效合力及其对下端的力矩。
        segment_force = (upper.total_pressure + lower.total_pressure) * length / 2
        segment_moment = (2 * upper.total_pressure + lower.total_pressure) * length**2 / 6
        moments.append(moments[-1] + shears[-1] * length + segment_moment)
        shears.append(shears[-1] + segment_force)

    max_moment_index = max(range(len(moments)), key=lambda index: abs(moments[index]))
    max_shear_index = max(range(len(shears)), key=lambda index: abs(shears[index]))
    return WallAnalysisResult(
        depths=depths,
        moments=moments,
        shears=shears,
        displacements=[0.0] * len(depths),
        max_moment=moments[max_moment_index],
        max_shear=shears[max_shear_index],
        max_moment_depth=depths[max_moment_index],
        max_shear_depth=depths[max_shear_index],
        method=WallAnalysisMethod.CANTILEVER,
        spring_profile=None,
    )


def analyze_wall_m_method(
    wall_model: WallModel,
    pressure_diagram: PressureDiagram,
    spring_profile: SpringProfile,
) -> WallAnalysisResult:
    """求简化线性梁-弹簧模型的位移、弯矩和剪力。

    网格等距；用二阶差分曲率构造 K_wall，用采样的 k 与节点分担长度
    构造 K_spring。将墙底两个节点的位移固定为零以近似固定端。
    压力按分段线性分布等效为节点荷载 F，解 (K_wall+K_spring)u=F。
    内力按相同差分曲率模型恢复，结果 status 为 complete。
    这是基础线性框架，不包含开挖面、施工阶段或支撑边界条件。
    """

    nodes = wall_model.nodes
    elements = wall_model.elements
    if len(nodes) < 3 or len(elements) != len(nodes) - 1 or not all(
        isinstance(element, BeamElement2D) for element in elements
    ):
        raise ValueError("m 法模型需要至少两个由 generate_mesh() 生成的梁单元")
    depths = [node.depth for node in nodes]
    lengths = [right - left for left, right in zip(depths, depths[1:])]
    if not isclose(depths[0], 0.0, abs_tol=1e-9) or any(
        not isfinite(length) or length <= 0 for length in lengths
    ) or any(not isclose(length, lengths[0], rel_tol=1e-9) for length in lengths):
        raise ValueError("m 法模型需要从深度 0 开始的等距网格")
    if any(
        element.node_i is not nodes[index]
        or element.node_j is not nodes[index + 1]
        or not isfinite(element.EI)
        or element.EI <= 0
        for index, element in enumerate(elements)
    ):
        raise ValueError("梁单元连接或 EI 无效")

    points = pressure_diagram.points
    if len(points) < 2 or not isclose(points[0].depth, 0.0, abs_tol=1e-9) or not isclose(
        points[-1].depth, depths[-1], rel_tol=1e-9, abs_tol=1e-9
    ):
        raise ValueError("压力分布必须覆盖整个墙高")
    if any(not isfinite(point.depth) or not isfinite(point.total_pressure) for point in points) or any(
        right.depth < left.depth for left, right in zip(points, points[1:])
    ):
        raise ValueError("压力点必须按深度递增且为有限数值")

    size = len(nodes)
    step = lengths[0]
    k_wall = np.zeros((size, size), dtype=float)
    k_spring = np.zeros((size, size), dtype=float)
    force = np.zeros(size, dtype=float)

    # 曲率能量 1/2 * EI * h * [(u[i-1]-2u[i]+u[i+1])/h²]²。
    for index in range(1, size - 1):
        ei = (elements[index - 1].EI + elements[index].EI) / 2
        stencil = np.array([1.0, -2.0, 1.0])
        k_wall[index - 1 : index + 2, index - 1 : index + 2] += ei / step**3 * np.outer(stencil, stencil)

    for index, node in enumerate(nodes):
        spring = spring_profile.get_spring_at_depth(node.depth)
        node.spring = spring
        tributary_length = step / 2 if index in (0, size - 1) else step
        k_spring[index, index] = spring.k * tributary_length

    # 对各压力线段与梁单元的交叠区间作 Simpson 积分，兼容层界处的压力跳变。
    for index, (top, bottom) in enumerate(zip(depths, depths[1:])):
        for left, right in zip(points, points[1:]):
            width = right.depth - left.depth
            if width <= 0:
                continue
            start = max(top, left.depth)
            end = min(bottom, right.depth)
            if end <= start:
                continue

            def pressure_at(depth: float) -> float:
                return left.total_pressure + (right.total_pressure - left.total_pressure) * (
                    (depth - left.depth) / width
                )

            middle = (start + end) / 2
            for node_index, shape in ((index, lambda z: (bottom - z) / step), (index + 1, lambda z: (z - top) / step)):
                force[node_index] += (end - start) / 6 * (
                    shape(start) * pressure_at(start)
                    + 4 * shape(middle) * pressure_at(middle)
                    + shape(end) * pressure_at(end)
                )

    stiffness = k_wall + k_spring
    displacement = np.zeros(size, dtype=float)
    free_count = size - 2
    try:
        displacement[:free_count] = np.linalg.solve(stiffness[:free_count, :free_count], force[:free_count])
    except np.linalg.LinAlgError as error:
        raise ValueError("梁-弹簧线性方程组无法求解") from error
    if not np.all(np.isfinite(displacement)):
        raise ValueError("梁-弹簧线性求解产生非有限位移")
    for node, value in zip(nodes, displacement):
        node.displacement = float(value)

    element_forces = [calculate_beam_forces(element, displacement) for element in elements]
    moment_sums = np.zeros(size, dtype=float)
    moment_counts = np.zeros(size, dtype=int)
    for index, (element, internal) in enumerate(zip(elements, element_forces)):
        half_difference = internal.shear * element.length / 2
        moment_sums[index] += internal.moment - half_difference
        moment_sums[index + 1] += internal.moment + half_difference
        moment_counts[index : index + 2] += 1
    moments = moment_sums / moment_counts
    shears = np.array(
        [element_forces[0].shear]
        + [(left.shear + right.shear) / 2 for left, right in zip(element_forces, element_forces[1:])]
        + [element_forces[-1].shear],
        dtype=float,
    )
    max_moment_index = int(np.argmax(np.abs(moments)))
    max_shear_index = int(np.argmax(np.abs(shears)))

    return WallAnalysisResult(
        depths=depths,
        moments=[float(value) for value in moments],
        shears=[float(value) for value in shears],
        displacements=[float(value) for value in displacement],
        max_moment=float(moments[max_moment_index]),
        max_shear=float(shears[max_shear_index]),
        max_moment_depth=depths[max_moment_index],
        max_shear_depth=depths[max_shear_index],
        method=WallAnalysisMethod.M_METHOD,
        spring_profile=spring_profile,
        status="complete",
        incomplete=False,
    )
