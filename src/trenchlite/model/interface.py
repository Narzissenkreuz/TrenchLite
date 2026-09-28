"""墙土界面几何与摩擦参数。"""

from dataclasses import dataclass


@dataclass
class WallInterface:
    """保存 Coulomb 主动压力所需角度，单位为度。

    wall_angle 从竖直方向量起，向填土侧倾斜为正；slope_angle 从
    水平方向量起，地面背离墙体向上升高为正。
    """

    delta: float = 0.0
    wall_angle: float = 0.0
    slope_angle: float = 0.0
