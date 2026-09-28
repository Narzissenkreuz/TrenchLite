"""围护墙截面基础线弹性弯曲验算。"""

from math import isfinite

from ..model.wall import WallSection
from ..result import SectionCheckResult


def check_bending_stress(moment: float, section: WallSection) -> SectionCheckResult:
    """按 σ=|M|/W 计算弯曲应力及允许应力利用率。

    M 以 kN·m/m、W 以 m³/m 输入，输出应力为 kPa。material_strength
    为用户指定的允许应力 kPa；当前不考虑轴力、剪应力或稳定折减。
    """

    modulus = section.section_modulus
    strength = section.material_strength
    if not isfinite(moment):
        raise ValueError("弯矩必须为有限数值")
    if modulus is None or not isfinite(modulus) or modulus <= 0:
        raise ValueError("截面模量 W 必须为正的有限数值")
    if strength is None or not isfinite(strength) or strength <= 0:
        raise ValueError("允许应力必须为正的有限数值")
    stress = abs(moment) / modulus
    return SectionCheckResult(max_stress=stress, allowable_stress=strength, utilization=stress / strength)
