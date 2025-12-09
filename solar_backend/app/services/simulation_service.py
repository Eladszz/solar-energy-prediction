import math

def calculate_poa(irradiance, latitude, tilt):
    """
    Approximate Plane-of-Array irradiance using simple cosine model.
    """
    angle_diff = abs(latitude - tilt)
    cos_factor = math.cos(math.radians(angle_diff))
    return irradiance * max(cos_factor, 0)


def calculate_cell_temp(irradiance, ambient_temp, noct):
    """
    Estimate cell temperature using standard NOCT model.
    """
    return ambient_temp + ((noct - 20) / 800) * irradiance


def calculate_power_kw(irradiance, t_cell, panel_area, efficiency, gamma):
    """
    Realistic power calculation including thermal derating.
    """
    stc_temp = 25
    thermal_factor = 1 - gamma * (t_cell - stc_temp)
    thermal_factor = max(thermal_factor, 0)  # avoid negative

    power_watts = irradiance * panel_area * efficiency * thermal_factor
    return power_watts / 1000  # kW


def simulate_production_enhanced(
    irradiance_list,
    temp_list,
    latitude,
    tilt,
    panel_area,
    efficiency,
    gamma,
    noct
):
    results_kw = []

    for irr, temp in zip(irradiance_list, temp_list):

        # Plane-of-array correction
        poa = calculate_poa(irr, latitude, tilt)

        # Cell temperature
        t_cell = calculate_cell_temp(irr, temp, noct)

        # Output power
        power_kw = calculate_power_kw(poa, t_cell, panel_area, efficiency, gamma)

        results_kw.append(power_kw)

    return results_kw
