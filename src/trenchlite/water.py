"""地下水数据模型。"""

from dataclasses import dataclass


@dataclass
class Groundwater:
    """记录地下水位标高及名称。"""

    elevation: float
    name: str
