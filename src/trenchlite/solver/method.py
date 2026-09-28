"""土压力计算方法的选择。"""

from enum import Enum


class EarthPressureMethod(Enum):
    """可选的主动土压力计算方法。"""

    RANKINE_ACTIVE = "rankine_active"
    COULOMB_ACTIVE = "coulomb_active"
