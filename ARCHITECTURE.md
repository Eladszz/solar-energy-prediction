# Architecture

## System Purpose

The Solar Energy Prediction System estimates solar energy production for a user-defined PV system and location. The Alpha version supports:
- 24-hour operational simulation from forecast weather
- Yearly forecast generation
- A physical baseline forecast path
- A real ML-based yearly forecast path
- A naive climatology benchmark baseline
- Financial value estimation from predicted kWh
- Financial decision-support using tariff and simple CAPEX assumptions
- Scenario comparison, benchmark evaluation, and backtest accuracy analysis

## High-Level Architecture

The system is split into two runtime components:

1. FastAPI backend
   - Exposes REST endpoints
   - Retrieves weather data from Open-Meteo
   - Runs physical PV simulation
   - Trains and executes the ML baseline yearly forecast
   - Computes financial summaries, benchmark metrics, and accuracy metrics

2. React frontend (`solar_frontend`)
   - Collects location and system inputs
   - Visualizes yearly, daily, comparison, benchmark, and accuracy outputs
   - Displays model metadata, tariff assumptions, and fallback messages
   - Supports map-based roof area selection
   - Uses Vite for local development and production builds

The repository also retains `solar_ui`, the previous Streamlit frontend. It is legacy code, is not part of the current runtime architecture, and remains in the repository temporarily for reference.

External dependency:
- Open-Meteo forecast and archive APIs

## Main Modules

### Backend routers

- `simulate_router.py`
  - Daily production simulation from forecast weather
- `yearly_forecast_router.py`
  - Yearly forecast for `physical` or `ml` mode
- `scenario_comparison_router.py`
  - Multi-scenario yearly comparison
- `accuracy_router.py`
  - Backtest against archived actual weather
- `benchmark_router.py`
  - Historical benchmark study across physical, ML, and naive baselines
- `health_router.py`
  - Basic service status endpoint

### Backend services

- `weather_service.py`
  - Retrieves short-range forecast weather
- `weather_archive_service.py`
  - Retrieves archived hourly weather by year
- `simulation_service.py`
  - Converts irradiance and temperature into AC output
- `loss_service.py`
  - Computes aggregate system loss factor from cleanliness and shading
- `yearly_forecast_service.py`
  - Orchestrates yearly weather profile preparation and yearly energy aggregation
- `ml_forecast_service.py`
  - Trains a ridge-regression weather model from historical hourly data
- `finance_service.py`
  - Converts energy outputs to estimated value, annual savings, and simple payback
- `scenario_comparison_service.py`
  - Reuses one yearly weather profile across multiple scenarios
- `accuracy_service.py`
  - Compares predicted and actual outputs and calculates MAPE
- `benchmark_service.py`
  - Evaluates physical, ML, and naive baselines across multiple completed years

### Frontend modules

- `solar_frontend/src/App.tsx`
  - Main React user workflow, input controls, map interaction, and result visualization
- `solar_frontend/src/main.tsx`
  - React application entry point
- `solar_frontend/lib/solar-api.ts`
  - Typed backend API payloads, responses, and request helpers
- `solar_frontend/src/index.css`
  - Application styling and theme definitions

### Legacy frontend

- `solar_ui/`
  - Previous Streamlit UI retained temporarily for reference
  - Not used by the current application or deployment flow

## Data Flow

### Daily simulation flow

1. User selects a location and system configuration in the React frontend.
2. Frontend sends `POST /simulate`.
3. Backend pulls hourly forecast weather.
4. Backend applies:
   - POA approximation
   - NOCT cell temperature model
   - thermal derating
   - system loss factor
   - inverter clipping
5. Backend returns hourly AC output, daily kWh, and estimated daily value.

### Yearly forecast flow

1. User selects forecast year, model type, and tariff assumption.
2. Frontend sends `POST /forecast/yearly`.
3. Backend builds a yearly weather profile:
   - `physical`: archived weather baseline
   - `ml`: trained weather regression forecast
4. Backend runs the physical PV conversion stack over the yearly hourly weather profile.
5. Backend aggregates monthly and yearly kWh.
6. Backend converts energy to estimated monthly and yearly value.
7. Backend returns forecast data plus metadata about:
   - forecast year
   - model requested and used
   - archived weather reference year
   - ML training years
   - fallback reason if any

### Benchmark flow

1. User selects a benchmark end year and historical window in the React frontend.
2. Frontend sends `POST /evaluation/benchmark`.
3. Backend builds a reference production proxy for each completed evaluation year by replaying archived actual weather through the shared PV simulation stack.
4. Backend evaluates three approaches for each year:
   - `physical`: prior-year archived weather baseline
   - `ml`: lightweight weather regression forecast
   - `naive`: historical climatology average aligned to the target year
5. Backend aggregates:
   - monthly MAPE
   - monthly MAE
   - yearly MAPE
   - yearly MAE
   - signed bias
6. Backend returns a comparison-ready response with per-approach metrics, per-year results, fallback years, and benchmark methodology notes.

## Forecasting Logic

### Physical path

The physical path is the deterministic baseline:
- input weather: archived hourly shortwave radiation and temperature
- POA approximation from latitude and tilt
- cell temperature estimation with NOCT
- power reduction using temperature coefficient
- loss adjustment
- inverter clipping

This path is reliable, transparent, and serves as:
- the baseline forecast
- the fallback path when ML is unavailable
- the energy conversion layer for both yearly modes

## Benchmarking Logic

The benchmark intentionally stays lightweight and reviewer-safe:

- All approaches share the same downstream PV conversion stack so the comparison isolates the weather-profile forecasting choice rather than mixing different production models.
- The benchmark reference is not utility-grade telemetry. It is a production proxy produced from archived actual weather and the configured PV system parameters.
- The `naive` baseline uses a calendar-aligned climatology from the recent training window. This provides a simple sanity-check baseline for the ML path.
- If the ML path cannot be trained for a benchmark year, the response records the fallback year explicitly instead of silently hiding the issue.

This makes the project academically stronger because it demonstrates:
- one deterministic physical baseline
- one learned forecasting baseline
- one intentionally simple naive baseline
- quantitative comparison across historical periods instead of anecdotal single-run results

## ML Integration

The Alpha ML path is intentionally simple and real:

- Training target:
  - archived hourly irradiance
  - archived hourly temperature
- Training data:
  - previous archived weather years for the selected location
- Features:
  - hour-of-day harmonics
  - day-of-year harmonics
  - month indicators
  - daylight proxy
  - year trend
- Model:
  - lightweight ridge regression implemented with NumPy

The ML model predicts an hourly weather profile for the target year. The system then passes that predicted weather into the same PV simulation pipeline used by the physical baseline. This keeps the architecture modular:
- ML predicts the weather profile
- the physics model converts weather to PV output

This design keeps the Alpha version:
- real
- explainable
- testable
- easy to extend later with richer models

## Monetary Estimation Logic

Financial outputs are computed from forecasted energy using intentionally simple assumptions:

- input:
  - `electricity_price_per_kwh`
  - `currency`
  - `system_capex`
- output:
  - monthly estimated value
  - yearly estimated value
  - annual savings
  - simple payback period
  - average monthly estimated value

Current financial assumptions:

- annual savings are treated as equal to yearly estimated value at the configured flat tariff
- simple payback is `system_capex / annual_savings`
- the model ignores degradation, financing, maintenance, taxes, export caps, and time-varying tariff plans

The tariff and CAPEX assumptions are returned in the backend response under `financial_assumptions`. This keeps the monetary estimate transparent and suitable for scenario comparison.

## Frontend / Backend Responsibilities

### Frontend responsibilities

- address entry and geocoding
- optional roof rectangle selection
- parameter collection
- forecast model selection
- tariff input
- CAPEX input
- result visualization
- scenario setup
- invoking backtest analysis

### Backend responsibilities

- data retrieval
- numerical forecasting and simulation
- ML training and prediction
- fallback behavior
- value estimation
- response shaping for the UI

## Current Alpha Scope

Included in Alpha:
- end-to-end demo flow
- physical and ML yearly forecasts
- benchmark study comparing physical, ML, and naive baselines
- daily simulation
- scenario comparison
- backtest accuracy with MAPE
- tariff-based monetary estimation
- annual savings and simple payback estimation
- automated test coverage for core services

Not included in Alpha:
- database persistence
- user accounts
- actual utility tariff catalogs by region
- plant monitoring integration
- advanced neural or probabilistic forecasting models

## Future Extensions

- direct learning from real PV production datasets
- better solar geometry and irradiance decomposition
- battery and storage modeling
- tariff plans with time-of-use pricing
- confidence intervals and uncertainty bands
- forecast history persistence and experiment tracking

## Related Artifacts

- `architecture/*.puml` contains the project diagrams used for the engineering report.
