"""按地表至坑底顺序排列的土层剖面。"""

from dataclasses import dataclass
from math import isfinite

from ..soil import SoilLayer


@dataclass
class SoilProfile:
    """保存按深度顺序排列的土层；每层厚度必须为正。"""

    layers: list[SoilLayer]

    def __post_init__(self) -> None:
        """校验剖面至少包含一个具有有效厚度的土层。"""

        if not self.layers:
            raise ValueError("土层剖面不能为空")
        if any(not isfinite(layer.thickness) or layer.thickness <= 0 for layer in self.layers):
            raise ValueError("每层土的厚度必须为正的有限数值")

    @property
    def total_depth(self) -> float:
        """返回全部土层的总厚度，单位为 m。"""

        return sum(layer.thickness for layer in self.layers)

    def get_layer_at_depth(self, depth: float) -> SoilLayer:
        """返回深度所在土层；分界点归入下层，坑底归入最末层。"""

        if not isfinite(depth) or not 0 <= depth <= self.total_depth:
            raise ValueError(f"深度必须位于 0 至 {self.total_depth} m 范围内")
        bottom = 0.0
        for layer in self.layers[:-1]:
            bottom += layer.thickness
            if depth < bottom:
                return layer
        return self.layers[-1]
