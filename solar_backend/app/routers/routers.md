# Router Documentation

This document matches the currently mounted FastAPI routes in `app/main.py`.

## Documentation Endpoints

- Swagger UI: `http://localhost:8000/swagger`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Exposed Routes

### `GET /`

Root status message for quick manual checks.

Response model: `RootResponse`

### `GET /health`

Health endpoint.

Response model: `HealthResponse`

Example:

```bash
curl http://localhost:8000/health
```

### `POST /simulate`

Runs the 24-hour forecast-weather simulation path.

Request model: `SimulationRequest`

Response model: `SimulationResponse`

Example:

```bash
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 32.08,
    "longitude": 34.78,
    "panel_area": 80.0,
    "panel_efficiency": 0.20,
    "cleanliness": "normal",
    "shading": "low",
    "ac_capacity_kw": 15.0
  }'
```

### `POST /forecast/yearly`

Runs the yearly forecast path for either the `physical` or `ml` model.

Request model: `YearlyForecastRequest`

Response model: `YearlyForecastResponse`

Example:

```bash
curl -X POST http://localhost:8000/forecast/yearly \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 32.08,
    "longitude": 34.78,
    "year": 2026,
    "tilt": 30.0,
    "panel_area": 80.0,
    "panel_efficiency": 0.20,
    "cleanliness": "normal",
    "shading": "low",
    "ac_capacity_kw": 15.0,
    "model_type": "ml",
    "training_years": 3,
    "electricity_price_per_kwh": 0.17,
    "currency": "USD"
  }'
```

### `POST /scenarios/compare`

Compares multiple PV configurations under the same location and forecast context.

Request model: `List[BasePVRequest]`

Response model: `ScenarioComparisonResponse`

Notes:

- at least two scenarios are required
- all scenarios must share latitude/longitude
- all scenarios must share model type, currency, and tariff assumption

### `POST /evaluation/accuracy`

Backtests the selected forecasting path against archived weather for a completed year.

Request model: `AccuracyEvaluationRequest`

Response model: `AccuracyEvaluationResponse`

## Mounted Prefixes

The backend mounts routers exactly as follows:

```python
app.include_router(health_router.router)
app.include_router(simulate_router.router, prefix="/simulate", tags=["Day Simulation"])
app.include_router(yearly_forecast_router.router, prefix="/forecast/yearly", tags=["Yearly Forecast"])
app.include_router(scenario_comparison_router.router, prefix="/scenarios", tags=["Scenario Comparison"])
app.include_router(accuracy_router.router, prefix="/evaluation", tags=["Accuracy Evaluation"])
```

`/simulate` and `/forecast/yearly` are mounted without requiring a trailing slash.
