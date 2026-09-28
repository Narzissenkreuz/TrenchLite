from dataclasses import dataclass


@dataclass
class SoilLayer:
    """记录单个土层的基本参数。"""

    name: str
    thickness: float
    gamma: float
    c: float
    phi: float
    m: float | None = None
