"""支护结构数据模型。"""

from dataclasses import dataclass


@dataclass
class Wall:
    """记录支护墙的名称和截面参数。"""

    name: str
    EI: float
    W: float


@dataclass
class Strut:
    """记录一道支撑的基本信息。"""

    name: str
    elevation: float
    section: str
