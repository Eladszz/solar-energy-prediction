# Testing Strategy

## Main End-to-End Flows

The Alpha version should be tested around the demo-critical workflows:

1. Baseline yearly forecast
   - Choose a location
   - Enter PV system parameters
   - Run a `physical` yearly forecast
   - Verify monthly kWh, yearly kWh, and yearly value are shown

2. ML yearly forecast
   - Switch to `ml`
   - Run the forecast again
   - Verify the response includes ML metadata or a fallback message

3. Daily simulation
   - Run the forecast flow
   - Open the Daily Simulation tab
   - Verify hourly AC power, daily kWh, and daily value

4. Scenario comparison
   - Add at least one modified scenario
   - Run comparison
   - Verify yearly energy, yearly value, and delta percentages

5. Accuracy backtest
   - Run the backtest for a year with archived weather available
   - Verify monthly predicted vs actual output and MAPE summary

## Functional Test Coverage

Automated backend coverage currently focuses on:
- weather retrieval and archive parsing
- PV simulation math
- yearly aggregation
- loss factor calculation
- financial summary calculation
- ML weather model training and prediction
- scenario comparison service behavior
- accuracy backtest service behavior

Recommended command:

```bash
cd solar_backend
pytest -q
```

Current result in this repository state:
- `176 passed`
- `1 skipped`

The skipped test is the live weather API check, which is intentionally skipped when internet access is unavailable in the test environment.

## Non-Functional Considerations

### Reliability

- The backend should return clear error messages when weather or geocoding services fail
- ML forecast failure should fall back to the physical baseline and state that explicitly

### Performance

- The chosen ML model is lightweight enough for interactive use
- Scenario comparison reuses a single yearly weather profile to avoid repeated weather generation per scenario

### Maintainability

- Forecast orchestration is separated from finance logic and ML logic
- Tests are service-focused and avoid unnecessary coupling to the UI

## Suggested Demo Scenarios

### Demo 1: Baseline system

- Location: Tel Aviv or another clear urban address
- Panel area: 80 m²
- Model: `physical`
- Goal: show standard yearly and daily forecast flow

### Demo 2: ML forecast path

- Same location and system
- Model: `ml`
- Goal: demonstrate the real ML forecasting option and metadata

### Demo 3: Scenario comparison

- Baseline system
- Scenario A: +20% panel area
- Scenario B: higher AC capacity
- Goal: show engineering tradeoff discussion with energy and value impact

### Demo 4: Accuracy backtest

- Run the accuracy tab for the latest completed archive year
- Goal: show predicted vs actual monthly output and MAPE

## Manual Validation Checklist

- Backend starts without import errors
- Frontend opens and can reach the backend
- Address lookup works
- Roof rectangle updates panel area
- Forecast results include financial assumptions
- ML forecast either runs or falls back cleanly
- Scenario comparison produces non-empty result tables
- Accuracy tab displays charts and metrics
