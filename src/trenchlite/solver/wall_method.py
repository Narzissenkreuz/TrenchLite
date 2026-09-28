"""围护墙分析方法选项。"""

from enum import Enum


class WallAnalysisMethod(Enum):
    """可选的围护墙分析方法。"""

    CANTILEVER = "cantilever"  # 已实现的简化悬臂墙积分分析。
    M_METHOD = "m_method"  # 仅建立土弹簧参数框架，尚无结构求解。
