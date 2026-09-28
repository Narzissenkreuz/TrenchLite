"""荷载数据模型。"""

from dataclasses import dataclass


@dataclass
class Load:
    """记录荷载名称和数值。"""

    name: str
    value: float
