"""沿深度分布的水平土弹簧参数。"""

from bisect import bisect_right
from dataclasses import dataclass
from math import isfinite


@dataclass
class SoilSpring:
    """记录某深度的水平抗力参数 k；当前尚非结构节点刚度。"""

    depth: float
    k: float


@dataclass
class SpringProfile:
    """保存按深度递增排列的水平土弹簧采样点。"""

    springs: list[SoilSpring]

    def __post_init__(self) -> None:
        """校验采样点参数及深度顺序。"""

        if any(
            not isfinite(spring.depth)
            or not isfinite(spring.k)
            or spring.depth < 0
            or spring.k < 0
            for spring in self.springs
        ):
            raise ValueError("土弹簧深度和 k 必须为非负有限数值")
        if any(right.depth <= left.depth for left, right in zip(self.springs, self.springs[1:])):
            raise ValueError("土弹簧深度必须严格递增")

    def get_spring_at_depth(self, depth: float) -> SoilSpring:
        """返回不深于指定深度的最近采样点；范围外抛出异常。"""

        if not self.springs:
            raise ValueError("土弹簧剖面为空")
        depths = [spring.depth for spring in self.springs]
        if not isfinite(depth) or not depths[0] <= depth <= depths[-1]:
            raise ValueError(f"深度必须位于 {depths[0]} 至 {depths[-1]} m 范围内")
        return self.springs[bisect_right(depths, depth) - 1]
