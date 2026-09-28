# TrenchLite

TrenchLite 是一个轻量化、开源的狭长沟槽基坑支护计算工具。项目计划逐步支持土压力计算、支护结构分析、钢支撑与围檩验算、稳定验算，以及计算书和附图的自动生成。

## 当前阶段：Phase 2.6

Phase 0.1 建立了软件工程结构和基础数据模型。Phase 0.2 增加地下水模型、截面模型和统一的计算结果接口。Phase 1.0 增加单层无水、无黏性土的 Rankine 主动土压力计算。Phase 1.1 增加均布超载与单一水平地下水面的侧压力分量。Phase 1.2 新增 `PressurePoint` 和 `PressureDiagram` 侧压力分布模型。Phase 1.3 让每个压力点分别保存土、超载、水和总侧压力，并支持各分量积分。Phase 1.4 新增 `SoilProfile`，支持多层土主动侧压力计算。Phase 1.5 新增计算方法接口与独立的 Rankine 系数函数。Phase 2.0 实现 Coulomb 主动土压力系数，`WallInterface` 提供墙土摩擦角、墙背倾角和地面坡角；默认方法仍为 Rankine。层界两侧各保留一个压力点，结果中的 `Ka` 表示坑底土层系数。有地下水时，各层 `gamma` 视为相应土层的有效重度，水压力另行相加。当前仅支持 `c=0` 和单一水平地下水面。

Coulomb 角度以度输入：`wall_angle` 为墙背从竖直向填土侧倾斜的角度，`slope_angle` 为地面背离墙体向上升高的角度。系数采用 [FHWA GEC 6 式 (6-2)](https://www.fhwa.dot.gov/engineering/geotech/pubs/010943.pdf)。当前结果仍表示沿深度的等效侧压力及其水平合力，不分解墙面倾角和摩擦产生的力方向。

Phase 2.1 增加二维围护结构模型基础：`WallSection` 保存截面刚度，`WallElement` 表示简化梁单元，`WallModel` 组合既有 `Wall` 与梁单元。Phase 2.2 实现顶部自由、底部固定的简化悬臂墙受力分析：`analyze_wall()` 沿深度积分压力分布，输出剪力、弯矩及最大值所在深度。墙高取所有 `WallElement.length` 之和；位移当前返回零占位值。此分析不考虑土反力、支撑或施工阶段。

Phase 2.3 新增 `WallAnalysisMethod`、可选土层 `m` 参数、`SoilSpring` 和 `SpringProfile`。`create_m_spring_profile()` 从土层剖面生成沿深度变化的水平抗力参数，当前按剖面顶部为零点取 `k=m·z`，并保留土层分界深度。接口尚无开挖面位置输入，生成的剖面参数是简化数据。

Phase 2.4 新增 `WallNode`、`BeamElement2D` 及 `WallModel.generate_mesh()`，建立等距二维梁-土弹簧离散模型。`analyze_wall_m_method()` 以二阶差分曲率构造墙体刚度、以各节点分担长度换算弹簧刚度，并将侧压力换算为节点荷载，用线性方程组求节点水平位移。墙底两个节点固定是当前简化边界条件。

Phase 2.5 根据同一差分曲率模型恢复 m 法的单元弯矩和剪力，并输出节点内力图及最大值。结果保留 `incomplete` 标记，本阶段求解结果设为 `False`；`status` 同步设为 `complete`。`WallSection` 增加截面模量和材料允许应力，`check_bending_stress()` 以 `|M|/W` 给出线弹性应力及利用率。输入弯矩为 kN·m/m、截面模量为 m³/m、允许应力为 kPa。围护墙求解尚无开挖面位置、支撑计算、分阶段结构求解和稳定验算；所得位移、内力及应力利用率仅用于验证简化线性流程，不能直接作为工程设计依据。

Phase 2.6 增加 `ConstructionSequence`，按顺序保存初始状态、分步开挖和支撑安装信息。`ExcavationStage` 增加可选说明，保留原有 `installed_struts` 字段和导入路径；`ExcavationProject` 可选保存施工序列。`analyze_stages()` 仅遍历阶段并返回 `StageResult`，其中 `analysis_available=False`，当前不按阶段重新求解，也不计算支撑刚度。施工序列为后续阶段分析提供数据结构。

## 运行示例和测试

在项目根目录安装本地包后运行：

```bash
python -m pip install -e .
python examples/example01.py
python -m unittest discover -s tests
```

## 后续计划

后续阶段将逐步扩展其他计算、验算和报告生成能力，并支持自动附图。
