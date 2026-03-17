# API Models Documentation

This backend uses two model groups:

- Request schemas in `requests.py`
- Response schemas in `responses.py`

## Request Schemas

### `BasePVRequest`

Shared request body for:

- `POST /simulate`
- `POST /forecast/yearly`
- `POST /evaluation/accuracy`

Validated fields:

- `latitude`: `-90.0` to `90.0`
- `longitude`: `-180.0` to `180.0`
- `year`: optional, `2000` to `2100`
- `tilt`: `0.0` to `90.0`
- `panel_area`: `> 0`
- `panel_efficiency`: `> 0` and `<= 1.0`
- `cleanliness`: `"clean" | "normal" | "dusty"`
- `shading`: `"none" | "low" | "medium" | "high"`
- `ac_capacity_kw`: `> 0`
- `gamma`: float
- `noct`: float
- `model_type`: `"physical" | "ml"`
- `electricity_price_per_kwh`: `>= 0`
- `currency`: `"USD" | "EUR" | "ILS"`
- `system_capex`: `>= 0`
- `training_years`: `1` to `10`

Additional request-contract behavior:

- extra JSON fields are rejected
- invalid values return FastAPI `422` validation errors

### Derived Request Schemas

- `SimulationRequest`: `POST /simulate`
- `YearlyForecastRequest`: `POST /forecast/yearly`
- `AccuracyEvaluationRequest`: `POST /evaluation/accuracy`

These currently inherit `BasePVRequest` without adding extra fields.

## Response Schemas

### `HealthResponse`

Used by `GET /health`.

### `RootResponse`

Used by `GET /`.

### `SimulationResponse`

Used by `POST /simulate`.

Key fields:

- `location`
- `system_loss_factor`
- `hourly_ac_kw`
- `avg_kw`
- `daily_kwh`
- `estimated_daily_value`
- `financial_assumptions`
- `timezone`
- `hourly_time`

### `YearlyForecastResponse`

Used by `POST /forecast/yearly`.

Key fields:

- `location`
- `forecast_year`
- `model_type_requested`
- `model_type_used`
- `weather_reference_year`
- `training_years_used`
- `monthly_kwh`
- `yearly_kwh`
- `specific_yield_kwh_per_kwp`
- `avg_daily_kwh`
- `monthly_estimated_value`
- `yearly_estimated_value`
- `annual_savings`
- `simple_payback_years`
- `avg_monthly_estimated_value`
- `financial_assumptions`
- `fallback_reason`
- `ml_metadata`

### `AccuracyEvaluationResponse`

Used by `POST /evaluation/accuracy`.

Key fields:

- `year`
- `model_type_requested`
- `model_type_used`
- `weather_reference_year`
- `training_years_used`
- `fallback_reason`
- `actual_yearly_kwh`
- `predicted_yearly_kwh`
- `actual_monthly_kwh`
- `predicted_monthly_kwh`
- `actual_annual_savings`
- `predicted_annual_savings`
- `actual_simple_payback_years`
- `predicted_simple_payback_years`
- `mape_percent`
- `yearly_mape_percent`
- `quality`
- `financial_assumptions`
- `ml_metadata`

### `ScenarioComparisonResponse`

Used by `POST /scenarios/compare`.

Key fields:

- `year`
- `model_type_requested`
- `model_type_used`
- `weather_reference_year`
- `training_years_used`
- `fallback_reason`
- `baseline_yearly_kwh`
- `baseline_yearly_estimated_value`
- `baseline_annual_savings`
- `baseline_simple_payback_years`
- `results`

Each `results` item is a `ScenarioComparisonResult` containing:

- the validated `scenario` payload
- yearly and monthly energy
- yearly and monthly estimated value
- annual savings and simple payback
- financial assumptions
- energy and value deltas versus baseline
