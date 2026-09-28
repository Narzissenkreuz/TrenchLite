"""可分解侧压力分布与各分量合力测试。"""

import unittest

from trenchlite import Groundwater, Load, SoilLayer
from trenchlite.solver import calculate_active_pressure


class PressureComponentTests(unittest.TestCase):
    def test_component_pressures_and_integrated_forces(self) -> None:
        soil = SoilLayer("砂土", thickness=5.0, gamma=18.0, c=0.0, phi=30.0)
        surcharge = Load("均布超载", 20.0)
        groundwater = Groundwater(elevation=-3.0, name="地下水位")
        result = calculate_active_pressure(soil, surcharge, groundwater)
        diagram = result.pressure_diagram

        for point in diagram.points:
            self.assertAlmostEqual(
                point.total_pressure,
                point.soil_pressure + point.surcharge_pressure + point.water_pressure,
            )

        forces = diagram.get_component_force()
        self.assertAlmostEqual(forces["soil_pressure"], result.soil_pressure)
        self.assertAlmostEqual(forces["surcharge_pressure"], result.surcharge_pressure)
        self.assertAlmostEqual(forces["water_pressure"], result.water_pressure)
        self.assertAlmostEqual(diagram.get_total_force(), result.total_force)


if __name__ == "__main__":
    unittest.main()
