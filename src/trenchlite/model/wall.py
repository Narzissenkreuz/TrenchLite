"""二维围护墙的截面与简化梁单元。"""

from dataclasses import dataclass

from ..structure import Wall


@dataclass
class WallSection:
    """保存二维围护墙截面刚度及可选的线弹性验算参数。"""

    name: str
    EI: float
    height: float
    section_modulus: float | None = None
    material_strength: float | None = None
    W: float | None = None

    def __post_init__(self) -> None:
        """允许通过 section_modulus 或工程常用符号 W 指定截面模量。"""

        if self.section_modulus is not None and self.W is not None and self.section_modulus != self.W:
            raise ValueError("section_modulus 与 W 必须一致")
        if self.section_modulus is None:
            self.section_modulus = self.W
        else:
            self.W = self.section_modulus


@dataclass
class WallElement:
    """保存简化梁单元长度及其关联的围护墙截面。"""

    length: float
    section: WallSection


__all__ = ["Wall", "WallSection", "WallElement"]
