import math

def calculate_power_kw(irradiance, t_cell, panel_area, efficiency, gamma):
    """
    Realistic power calculation including thermal derating.
    """
    stc_temp = 25
    thermal_factor = 1 - gamma * (t_cell - stc_temp)
    thermal_factor = max(thermal_factor, 0)  # avoid negative

    power_watts = irradiance * panel_area * efficiency * thermal_factor
    return power_watts / 1000  # kW

import math
from typing import List, Optional


def calculate_poa(ghi: float, latitude: float, tilt: float) -> float:
    """
    Approximates Plane-Of-Array irradiance using a simple incidence angle model.
    This is a first-order POA correction, not a full solar-geometry model.
    """
    # difference between tilt and latitude gives rough incidence correction
    angle_diff = abs(latitude - tilt)
    cos_factor = math.cos(math.radians(angle_diff))
    return max(ghi * max(cos_factor, 0.0), 0.0)


def calculate_cell_temp(poa: float, ambient_temp: float, noct: float) -> float:
    """
    Estimate cell temperature using the NOCT model:
    Tcell = Tambient + (NOCT - 20°C) / 800 * POA
    """
    return ambient_temp + ((noct - 20.0) / 800.0) * poa


def calculate_dc_power_kw(
    poa: float,
    t_cell: float,
    panel_area: float,
    efficiency_stc: float,
    gamma: float
) -> float:
    """
    Compute DC power output in kW.
    """
    stc_temp = 25.0
    thermal_factor = 1.0 - gamma * (t_cell - stc_temp)
    thermal_factor = max(thermal_factor, 0.0)

    dc_power_watts = poa * panel_area * efficiency_stc * thermal_factor
    return dc_power_watts / 1000.0


def apply_system_losses(dc_kw: float, system_loss_factor: float) -> float:
    """
    Apply aggregated system losses AFTER DC generation.
    Example: 0.86 means 14% total losses (soiling, mismatch, wiring, inverter eff., etc.)
    """
    return max(dc_kw * system_loss_factor, 0.0)


def apply_inverter_clipping(ac_kw: float, ac_capacity_kw: Optional[float]) -> float:
    """
    Limit AC power by inverter rated AC capacity.
    If ac_capacity_kw is None or <= 0 → no clipping applied.
    """
    if ac_capacity_kw is None or ac_capacity_kw <= 0:
        return ac_kw
    return min(ac_kw, ac_capacity_kw)



def simulate_production_enhanced(
    irradiance_list: List[float],
    temp_list: List[float],
    latitude: float,
    tilt: float,
    panel_area: float,
    efficiency: float,
    gamma: float,
    noct: float,
    system_loss_factor: float,
    ac_capacity_kw: Optional[float] = None,
) -> List[float]:
    """
    Full PV simulation:
    GHI → POA → T_cell → DC → Losses → AC_clipping
    Returns list of hourly AC power production in kW.
    """
    results_ac_kw = []

    for ghi, ambient_temp in zip(irradiance_list, temp_list):

        # 1. POA irradiance
        poa = calculate_poa(ghi, latitude, tilt)
        if poa <= 0.0:
            results_ac_kw.append(0.0)
            continue

        # 2. Cell temperature
        t_cell = calculate_cell_temp(poa, ambient_temp, noct)

        # 3. DC power
        dc_kw = calculate_dc_power_kw(
            poa=poa,
            t_cell=t_cell,
            panel_area=panel_area,
            efficiency_stc=efficiency,
            gamma=gamma
        )

        # 4. System losses
        ac_before_clip = apply_system_losses(dc_kw, system_loss_factor)

        # 5. Inverter clipping
        ac_kw = apply_inverter_clipping(ac_before_clip, ac_capacity_kw)

        results_ac_kw.append(ac_kw)

    return results_ac_kw

