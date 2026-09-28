"""创建一个测试工程并输出基本信息。"""

from trenchlite import (
    ConstructionSequence,
    EarthPressureMethod,
    ExcavationProject,
    ExcavationStage,
    Groundwater,
    Load,
    Section,
    SoilLayer,
    SoilProfile,
    Strut,
    Wall,
    WallElement,
    WallInterface,
    WallModel,
    WallSection,
)
from trenchlite.solver import (
    analyze_stages,
    analyze_wall,
    analyze_wall_m_method,
    calculate_active_pressure,
    check_bending_stress,
    create_m_spring_profile,
)


def main() -> None:
    soil = SoilLayer(name="砂土", thickness=5.0, gamma=18.0, c=0.0, phi=30.0)
    # 工程对象中的旧式墙截面参数仅作资料展示；m 法示例另设计算截面。
    wall = Wall(name="拉森IV型钢板桩", EI=0.0, W=0.0)
    strut = Strut(name="第一道支撑", elevation=-1.0, section="609×16钢管")
    groundwater = Groundwater(elevation=-3.0, name="地下水位")
    surcharge = Load(name="地面均布超载", value=20.0)
    # 截面参数仅用于展示数据接口，数值不用于计算。
    section = Section(name="609×16钢管", area=1.0, inertia=1.0, modulus=1.0)
    stage = ExcavationStage(name="开挖至坑底", excavation_depth=5.0, installed_struts=[strut])
    construction_sequence = ConstructionSequence()
    construction_sequence.add_stage(ExcavationStage("初始状态", 0.0))
    construction_sequence.add_stage(ExcavationStage("Stage 1：开挖 2 m", 2.0))
    construction_sequence.add_stage(
        ExcavationStage("Stage 2：开挖 5 m", 5.0, installed_struts=[strut], description="记录支撑安装状态")
    )
    project = ExcavationProject(
        name="Test Trench",
        depth=5.0,
        soils=[soil],
        wall=wall,
        struts=[strut],
        loads=[surcharge],
        stages=[stage],
        groundwater=groundwater,
        sections=[section],
        construction_sequence=construction_sequence,
    )

    print(f"工程名称：{project.name}")
    print(f"坑深：{project.depth} m")
    for layer in project.soils:
        print(f"土层：{layer.name}，厚度 {layer.thickness} m，重度 {layer.gamma}，黏聚力 {layer.c}，内摩擦角 {layer.phi}")
    print(f"支护：{project.wall.name}")
    for support in project.struts:
        print(f"支撑：{support.name}，标高 {support.elevation} m，截面 {support.section}")
    if project.groundwater is not None:
        print(f"地下水：{project.groundwater.name}，标高 {project.groundwater.elevation} m")
    for load in project.loads:
        print(f"荷载：{load.name}，{load.value} kPa")
    for section in project.sections:
        print(f"截面：{section.name}，面积 {section.area}，惯性矩 {section.inertia}，截面模量 {section.modulus}")
    print(f"施工阶段：{', '.join(stage.name for stage in project.stages)}")
    print("施工序列（仅数据遍历）：")
    for stage_result in analyze_stages(project):
        print(f"  {stage_result.stage_name}，开挖深度 {stage_result.excavation_depth} m")

    pressure = calculate_active_pressure(project.soils[0], project.loads[0], project.groundwater)
    print("\n主动侧压力计算结果：")
    print(f"主动土压力系数：Ka = {pressure.Ka:.3f}")
    print(f"土压力合力：{pressure.soil_pressure:.3f} kN/m")
    print(f"超载合力：{pressure.surcharge_pressure:.3f} kN/m")
    print(f"水压力合力：{pressure.water_pressure:.3f} kN/m")
    print(f"总合力：{pressure.total_force:.3f} kN/m")
    print(f"最大压力：{pressure.max_pressure:.3f} kPa")
    print(f"作用点距坑底：{pressure.application_depth:.3f} m")
    coulomb_pressure = calculate_active_pressure(
        project.soils[0],
        project.loads[0],
        project.groundwater,
        method=EarthPressureMethod.COULOMB_ACTIVE,
        wall_interface=WallInterface(delta=15.0),
    )
    print("\n方法比较：")
    for result in (pressure, coulomb_pressure):
        print(f"{result.method}：Ka={result.Ka:.3f}，总合力={result.total_force:.3f} kN/m")
    points = pressure.pressure_diagram.points
    print(f"压力分布：{len(points)} points")
    print("深度(m)  土压力(kPa)  超载压力(kPa)  水压力(kPa)  总压力(kPa)")
    for target_depth in (0.0, 2.5, 5.0):
        point = next(point for point in points if abs(point.depth - target_depth) < 1e-9)
        print(
            f"{point.depth:7.2f}  {point.soil_pressure:11.3f}"
            f"  {point.surcharge_pressure:13.3f}  {point.water_pressure:11.3f}"
            f"  {point.total_pressure:11.3f}"
        )

    profile = SoilProfile(
        [
            SoilLayer(name="填土", thickness=2.0, gamma=18.0, c=0.0, phi=20.0, m=100.0),
            SoilLayer(name="砂土", thickness=3.0, gamma=20.0, c=0.0, phi=30.0, m=200.0),
        ]
    )
    layered_project = ExcavationProject(
        name="Layered Trench",
        depth=5.0,
        soils=profile,
        wall=wall,
        loads=[surcharge],
        groundwater=groundwater,
    )
    layered_pressure = calculate_active_pressure(profile, surcharge, groundwater)
    print(f"\n分层工程：{layered_project.name}")
    print("0–2 m：填土；2–5 m：砂土")
    print("深度(m)  土压力(kPa)  超载压力(kPa)  水压力(kPa)  总压力(kPa)")
    for point in layered_pressure.pressure_diagram.points:
        if point.depth in (0.0, 1.0, 2.0, 3.0, 5.0):
            print(
                f"{point.depth:7.2f}  {point.soil_pressure:11.3f}"
                f"  {point.surcharge_pressure:13.3f}  {point.water_pressure:11.3f}"
                f"  {point.total_pressure:11.3f}"
            )

    wall_section = WallSection(
        name="示例墙截面", EI=1200.0, height=5.0,
        section_modulus=0.01, material_strength=200000.0,
    )
    wall_model = WallModel(wall=wall, elements=[WallElement(length=5.0, section=wall_section)])
    print("\n二维围护墙模型：")
    print(f"墙体：{wall_model.wall.name}")
    print(f"截面：{wall_section.name}，EI={wall_section.EI}，高度={wall_section.height} m")
    print(f"梁单元数量：{len(wall_model.elements)}")
    wall_result = analyze_wall(wall_model, pressure.pressure_diagram)
    print(f"最大弯矩：{wall_result.max_moment:.3f} kN·m/m，深度 {wall_result.max_moment_depth:.3f} m")
    print(f"最大剪力：{wall_result.max_shear:.3f} kN/m，深度 {wall_result.max_shear_depth:.3f} m")

    spring_profile = create_m_spring_profile(profile, wall_depth=5.0)
    print("\nm 法土弹簧参数示例：")
    for layer in profile.layers:
        print(f"土层：{layer.name}，m={layer.m}")
    print(f"生成的弹簧采样点数量：{len(spring_profile.springs)}")

    m_model = WallModel(wall=Wall(name="示例墙", EI=wall_section.EI, W=wall.W))
    m_model.generate_mesh(height=5.0, element_count=20)
    m_result = analyze_wall_m_method(m_model, layered_pressure.pressure_diagram, spring_profile)
    section_result = check_bending_stress(m_result.max_moment, wall_section)
    print("\n基础线性 m 法分析与截面验算：")
    print(f"节点数量：{len(m_model.nodes)}")
    print(f"最大水平位移：{max(abs(value) for value in m_result.displacements):.4f} m")
    print(f"最大弯矩：{abs(m_result.max_moment):.3f} kN·m/m")
    print(f"最大剪力：{abs(m_result.max_shear):.3f} kN/m")
    print(f"最大弯曲应力：{section_result.max_stress:.1f} kPa")
    print(f"截面应力利用率：{section_result.utilization:.3f}")


if __name__ == "__main__":
    main()
