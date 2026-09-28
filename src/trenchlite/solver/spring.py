"""从土层 m 参数生成水平抗力剖面。"""

from math import isfinite

from ..model.profile import SoilProfile
from ..model.spring import SoilSpring, SpringProfile


def create_m_spring_profile(profile: SoilProfile, wall_depth: float) -> SpringProfile:
    """从地表向下取样，并按 k(z)=m·z 生成水平抗力参数。

    生成 20 个等分区间，额外保留土层分界深度。此处 z 以剖面顶部为 0，
    k 尚未乘以节点分担长度或墙体计算宽度，不参与结构求解。
    """

    if not isfinite(wall_depth) or not 0 < wall_depth <= profile.total_depth:
        raise ValueError("墙深度必须为正且不超过土层剖面总厚度")

    depths = {wall_depth * index / 20 for index in range(21)}
    boundary = 0.0
    for layer in profile.layers[:-1]:
        boundary += layer.thickness
        if boundary < wall_depth:
            depths.add(boundary)

    springs: list[SoilSpring] = []
    for depth in sorted(depths):
        layer = profile.get_layer_at_depth(depth)
        if layer.m is None or not isfinite(layer.m) or layer.m < 0:
            raise ValueError(f"土层 {layer.name} 缺少有效的 m 参数")
        springs.append(SoilSpring(depth=depth, k=layer.m * depth))
    return SpringProfile(springs=springs)
