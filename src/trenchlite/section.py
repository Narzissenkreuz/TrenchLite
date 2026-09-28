"""截面数据模型。"""

from dataclasses import dataclass


@dataclass
class Section:
    """记录截面的基本几何参数。"""

    name: str
    area: float
    inertia: float
    modulus: float
