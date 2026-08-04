# Services

- `weather_service.py`: Open-Meteo next-day hourly forecast integration.
- `weather_archive_service.py`: Open-Meteo archived hourly weather integration.
- `external_service.py`: provider timeout and response validation.
- `simulation_service.py`: simplified POA, NOCT temperature, DC power, losses, and AC clipping.
- `loss_service.py`: cleanliness, shading, wiring, and inverter loss assumptions.
- `yearly_forecast_service.py`: hourly-profile validation, archive-year alignment, physical simulation, and monthly/yearly aggregation.
- `scenario_comparison_service.py`: one shared weather profile with independent system calculations.
- `finance_service.py`: flat-tariff value, annual savings, and simple payback.

Units: irradiance W/m²; area m²; instantaneous power W/kW; one-hour energy kWh; annual energy kWh/year; AC capacity kW.
