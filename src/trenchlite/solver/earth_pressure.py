"""单层及分层无黏性土的主动侧压力。"""

from bisect import bisect_right
from math import cos, isfinite, radians, sin, sqrt

from ..load import Load
from ..model import SoilProfile, WallInterface
from ..result import ActivePressureResult, PressureDiagram, PressurePoint
from ..soil import SoilLayer
from ..water import Groundwater
from .method import EarthPressureMethod


WATER_UNIT_WEIGHT = 9.8  # kN/m³


def calculate_rankine_active_coefficient(phi: float) -> float:
    """根据内摩擦角 phi（度）计算 Rankine 主动土压力系数。"""

    if not isfinite(phi) or not 0 <= phi < 90:
        raise ValueError("内摩擦角 phi 必须在 [0, 90) 度范围内")
    sine = sin(radians(phi))
    return (1 - sine) / (1 + sine)


def calculate_coulomb_active_coefficient(
    phi: float,
    delta: float,
    wall_angle: float,
    slope_angle: float,
) -> float:
    """根据度数角度计算 Coulomb 主动土压力系数。

    wall_angle 从竖直向填土侧为正；slope_angle 为背离墙体上升的坡角。
    采用 FHWA GEC 6 式 (6-2) 的通用 Coulomb 主动系数表达式。
    """

    if not all(isfinite(angle) for angle in (phi, delta, wall_angle, slope_angle)):
        raise ValueError("Coulomb 角度参数必须为有限数值")
    if not 0 <= phi < 90:
        raise ValueError("内摩擦角 phi 必须在 [0, 90) 度范围内")
    if not 0 <= delta <= phi:
        raise ValueError("墙土摩擦角 delta 必须在 [0, phi] 度范围内")
    if not -90 < wall_angle < 90 or not -90 < slope_angle <= phi:
        raise ValueError("墙背倾角或地面坡角超出 Coulomb 公式适用范围")

    phi_r, delta_r, theta, beta = map(radians, (phi, delta, wall_angle, slope_angle))
    wall_cosine = cos(theta + delta_r)
    slope_cosine = cos(theta - beta)
    if wall_cosine <= 0 or slope_cosine <= 0:
        raise ValueError("墙背与地面角度组合使 Coulomb 公式无效")

    # FHWA GEC 6 (6-2): Ka = cos²(φ-θ) / [cos²θ cos(θ+δ)
    #   × (1 + √(sin(φ+δ) sin(φ-β) / (cos(θ+δ) cos(θ-β))))²]
    root_term = sin(phi_r + delta_r) * sin(phi_r - beta) / (wall_cosine * slope_cosine)
    if root_term < 0:
        raise ValueError("Coulomb 公式根号内必须非负")
    denominator = cos(theta) ** 2 * wall_cosine * (1 + sqrt(root_term)) ** 2
    return cos(phi_r - theta) ** 2 / denominator


def calculate_active_pressure(
    soil: SoilLayer | SoilProfile,
    load: Load | None = None,
    groundwater: Groundwater | None = None,
    method: EarthPressureMethod = EarthPressureMethod.RANKINE_ACTIVE,
    wall_interface: WallInterface | None = None,
) -> ActivePressureResult:
    """计算单层或分层土的主动侧压力和各分量合力。

    method 默认使用 Rankine；Coulomb 使用 wall_interface 指定墙土摩擦、
    墙背倾角和地面坡角，省略时三个角度均为 0。所有土层 c=0。
    单层时 H 取 soil.thickness，分层时 H 取各层厚度之和。每层按自身的 gamma、phi
    计算，并将上覆各层的有效竖向应力累加；层界两侧分别保留压力点。
    结果中的单个 Ka 代表坑底土层。load.value 是均布超载 q（kPa）；
    地下水位标高以地表为 0、向下为负，支持单一水平水面。水重度固定
    为 9.8 kN/m³。

    gamma 以 kN/m³ 输入；有地下水时，它被视为全高统一的有效重度近似，
    静水压力单独相加，不处理水位上下不同重度。max_pressure 是分布点
    中的最大总侧压力（kPa），各合力单位为 kN/m；application_depth 从坑底向上量取。
    侧压力分布按地表至坑底的 20 个等分区间取点，并补入土层分界点
    及区间内的地下水位点。当前仅计算侧压力大小与水平合力，不分解
    墙面倾斜及墙土摩擦导致的力方向；不支持被动土压力。
    """

    if method is EarthPressureMethod.RANKINE_ACTIVE:
        coefficient = calculate_rankine_active_coefficient
        method_name = "Rankine"
    elif method is EarthPressureMethod.COULOMB_ACTIVE:
        interface = wall_interface if wall_interface is not None else WallInterface()

        def coefficient(phi: float) -> float:
            """按给定墙土界面参数返回 Coulomb 系数。"""

            return calculate_coulomb_active_coefficient(
                phi, interface.delta, interface.wall_angle, interface.slope_angle
            )

        method_name = "Coulomb"
    else:
        raise ValueError(f"不支持的土压力计算方法：{method}")

    profile = soil if isinstance(soil, SoilProfile) else SoilProfile([soil])
    layers = profile.layers
    for layer in layers:
        if not all(isfinite(value) for value in (layer.thickness, layer.gamma, layer.c, layer.phi)):
            raise ValueError("土层计算参数必须为有限数值")
        if layer.gamma < 0:
            raise ValueError("土层重度不能为负数")
        if layer.c != 0:
            raise ValueError("当前只支持 c=0 的无黏性土")
        if not 0 <= layer.phi < 90:
            raise ValueError("内摩擦角 phi 必须在 [0, 90) 度范围内")
    if load is not None and (not isfinite(load.value) or load.value < 0):
        raise ValueError("均布超载必须为非负有限数值")
    if groundwater is not None and (not isfinite(groundwater.elevation) or groundwater.elevation > 0):
        raise ValueError("地下水位标高必须为地表以下的有限数值")

    height = profile.total_depth
    layer_boundaries: list[float] = []
    boundary = 0.0
    for layer in layers[:-1]:
        boundary += layer.thickness
        layer_boundaries.append(boundary)

    def vertical_stress(depth: float) -> float:
        """累加深度以上各层的有效竖向应力。"""

        stress = 0.0
        top = 0.0
        for layer in layers:
            stress += layer.gamma * min(max(depth - top, 0.0), layer.thickness)
            top += layer.thickness
        return stress

    water_start_depth = -groundwater.elevation if groundwater is not None else height
    surcharge = load.value if load is not None else 0.0

    def make_point(depth: float, layer: SoilLayer) -> PressurePoint:
        """按指定土层系数生成该深度的分量压力。"""

        ka = coefficient(layer.phi)
        soil_pressure = ka * vertical_stress(depth)
        surcharge_pressure = ka * surcharge
        water_pressure = WATER_UNIT_WEIGHT * max(0.0, depth - water_start_depth)
        return PressurePoint(
            depth=depth,
            soil_pressure=soil_pressure,
            surcharge_pressure=surcharge_pressure,
            water_pressure=water_pressure,
            total_pressure=soil_pressure + surcharge_pressure + water_pressure,
        )

    depths = {height * index / 20 for index in range(21)}
    depths.update(layer_boundaries)
    if 0 < water_start_depth < height:
        depths.add(water_start_depth)

    points: list[PressurePoint] = []
    for depth in sorted(depths):
        if depth in layer_boundaries:
            lower_index = bisect_right(layer_boundaries, depth)
            points.append(make_point(depth, layers[lower_index - 1]))
            points.append(make_point(depth, layers[lower_index]))
        else:
            points.append(make_point(depth, profile.get_layer_at_depth(depth)))

    diagram = PressureDiagram(points=points, total_force=0.0, application_depth=0.0)
    forces = diagram.get_component_force()
    total_force = diagram.get_total_force()
    moment_about_base = sum(
        (right.depth - left.depth)
        * (
            (2 * left.total_pressure + right.total_pressure) * (height - left.depth)
            + (left.total_pressure + 2 * right.total_pressure) * (height - right.depth)
        )
        / 6
        for left, right in zip(points, points[1:])
    )
    application_depth = moment_about_base / total_force if total_force else 0.0
    diagram.total_force = total_force
    diagram.application_depth = application_depth

    return ActivePressureResult(
        name=f"{method_name} 主动土压力",
        Ka=coefficient(layers[-1].phi),
        max_pressure=max(point.total_pressure for point in points),
        total_force=total_force,
        application_depth=application_depth,
        soil_pressure=forces["soil_pressure"],
        surcharge_pressure=forces["surcharge_pressure"],
        water_pressure=forces["water_pressure"],
        pressure_diagram=diagram,
        method=method_name,
    )
