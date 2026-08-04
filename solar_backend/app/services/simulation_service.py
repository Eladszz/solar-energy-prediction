import math
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def calculate_poa(ghi: float, latitude: float, tilt: float) -> float:
    """
    Approximate plane-of-array irradiance in W/m² from GHI in W/m².
    This is a first-order POA correction, not a full solar-geometry model.
    """
    # difference between tilt and latitude gives rough incidence correction
    logger.debug(f"Calculating POA with GHI={ghi}, latitude={latitude}, tilt={tilt}")
    angle_diff = abs(latitude - tilt)
    logger.debug(f"Angle difference calculated as {angle_diff}")
    cos_factor = math.cos(math.radians(angle_diff))
    logger.debug(f"Cosine factor calculated as {cos_factor}")
    return max(ghi * max(cos_factor, 0.0), 0.0)


def calculate_cell_temp(poa: float, ambient_temp: float, noct: float) -> float:
    """
    Estimate cell temperature using the NOCT model:
    Tcell = Tambient + (NOCT - 20°C) / 800 * POA
    """
    logger.debug(
        f"Calculating cell temperature with POA={poa}, ambient_temp={ambient_temp}, NOCT={noct}"
    )
    return ambient_temp + ((noct - 20.0) / 800.0) * poa


def calculate_dc_power_kw(
    poa: float, t_cell: float, panel_area: float, efficiency_stc: float, gamma: float
) -> float:
    """
    Compute DC power in kW from irradiance (W/m²) and panel area (m²).
    """
    logger.debug(
        f"Calculating DC power with POA={poa}, t_cell={t_cell}, panel_area={panel_area}, efficiency_stc={efficiency_stc}, gamma={gamma}"
    )
    stc_temp = 25.0
    thermal_factor = 1.0 - gamma * (t_cell - stc_temp)
    thermal_factor = max(thermal_factor, 0.0)
    logger.debug(f"Thermal factor calculated as {thermal_factor}")
    dc_power_watts = poa * panel_area * efficiency_stc * thermal_factor
    logger.debug(f"DC power in watts calculated as {dc_power_watts}")
    return dc_power_watts / 1000.0


def apply_system_losses(dc_kw: float, system_loss_factor: float) -> float:
    """
    Apply aggregated system losses AFTER DC generation.
    Example: 0.86 means 14% total losses (soiling, mismatch, wiring, inverter eff., etc.)
    """
    logger.debug(
        f"Applying system losses with DC power={dc_kw}, system_loss_factor={system_loss_factor}"
    )
    return max(dc_kw * system_loss_factor, 0.0)


def apply_inverter_clipping(ac_kw: float, ac_capacity_kw: Optional[float]) -> float:
    """
    Limit AC power by inverter rated AC capacity.
    If ac_capacity_kw is None or <= 0 → no clipping applied.
    """
    logger.debug(
        f"Applying inverter clipping with AC power={ac_kw}, ac_capacity_kw={ac_capacity_kw}"
    )
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
    AC capacity and returned power are kW; each hourly sample represents kWh.
    """
    results_ac_kw = []
    logger.info("Starting enhanced PV production simulation...")
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
            gamma=gamma,
        )

        # 4. System losses
        ac_before_clip = apply_system_losses(dc_kw, system_loss_factor)

        # 5. Inverter clipping
        ac_kw = apply_inverter_clipping(ac_before_clip, ac_capacity_kw)
        logger.debug(
            f"Hour result - GHI: {ghi}, POA: {poa}, T_cell: {t_cell}, DC_kW: {dc_kw}, AC_before_clip: {ac_before_clip}, AC_kW: {ac_kw}"
        )
        results_ac_kw.append(ac_kw)
    logger.info(
        f"Enhanced PV production simulation completed. Processed {len(results_ac_kw)} hours."
    )

    return results_ac_kw
