# Routers

- `simulate_router.py`: validates a PV request, retrieves next-day Open-Meteo values, sanitizes missing irradiance/temperature, and returns hourly/daily physical output.
- `yearly_forecast_router.py`: retrieves one physical archive profile, calculates system losses, and returns monthly/yearly energy and finance.
- `scenario_comparison_router.py`: delegates a validated unique-name scenario request to the shared-weather comparison service.
- `health_router.py`: returns service health.

Routers translate known domain and provider failures to controlled HTTP responses. Numerical calculations remain in services.
