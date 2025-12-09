def simulate_production(irradiance_list: list, panel_efficiency: float, panel_area: float):
    """
    Very simple production formula:
    energy = irradiance(W/m2) * area(m2) * efficiency
    """
    production = []
    for irr in irradiance_list:
        kw = (irr * panel_area * panel_efficiency) / 1000  # Convert W → kW
        production.append(kw)
    return production
