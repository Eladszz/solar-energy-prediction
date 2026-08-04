# Architecture

## Runtime

The repository contains one product: a React/Vite frontend and FastAPI backend packaged in one Docker image. FastAPI serves both the built frontend and the API.

```text
Browser / React
  -> FastAPI request models and routers
  -> Open-Meteo forecast or archive weather
  -> weather validation
  -> system-loss calculation
  -> simplified physical PV simulation
  -> hourly/monthly/yearly aggregation
  -> flat-tariff financial calculation
  -> typed response and React charts
```

## Active endpoints

- `/simulate`: retrieves next-day hourly shortwave radiation and temperature, validates values, simulates hourly AC kW, and sums daily kWh.
- `/forecast/yearly`: chooses the requested archive year or latest complete reference year, validates hourly spacing, runs the physical model, and aggregates twelve months and one year.
- `/scenarios/compare`: builds one yearly weather profile and copies it for each independently configured PV system.
- `/health`: reports backend availability.

## Physical calculation

1. Shortwave radiation/GHI in W/m² is converted to approximate plane-of-array irradiance using latitude and tilt.
2. NOCT estimates cell temperature in °C.
3. Irradiance × panel area (m²) × efficiency × temperature factor gives DC W; division by 1000 gives kW.
4. Cleanliness, shading, wiring, and inverter assumptions form one multiplicative loss factor.
5. AC output is clipped to configured inverter capacity in kW.
6. Each validated one-hour AC-power sample contributes the same numeric value in kWh; values aggregate to kWh/month and kWh/year.

This is intentionally simplified: it does not model azimuth, full solar geometry, direct/diffuse decomposition, horizon, storage, or grid constraints.

## Weather behavior

Open-Meteo is the only weather provider. Daily simulation uses its forecast API. Yearly/scenario estimates use its archive API. The yearly response reports `weather_source`, `weather_reference_year`, and `requested_forecast_year`. Current/future years reuse the last complete archive year and return a clear reason.

Profiles are sorted, must have unique continuous hourly timestamps, and must contain usable numeric weather values before energy aggregation.

## Finance

Monthly energy is multiplied by the configured flat tariff. Annual savings equals annual estimated value, and simple payback equals CAPEX divided by annual savings. Currency is a display/contract label; no conversion is performed.

## Deployment

The Docker frontend stage runs `npm ci` and builds Vite assets. The Python runtime installs backend requirements, copies the backend/shared defaults/frontend assets, and starts Uvicorn on port 8000. No API key is required.
