# Demo Mode

Demo mode gives the project a stable presentation path without depending on live geocoding or weather providers.

## What It Does

- Replaces live geocoding with bundled scenario locations.
- Replaces forecast and archive weather calls with deterministic local fixtures.
- Keeps daily forecast, yearly forecast, scenario comparison, and accuracy backtest flows runnable even if third-party APIs are down.
- Labels the UI clearly whenever demo mode is active.

## Bundled Scenarios

- `tel_aviv_rooftop`: urban commercial rooftop in Tel Aviv
- `phoenix_distribution_center`: high-irradiance warehouse array in Phoenix
- `berlin_school_campus`: school rooftop with stronger seasonality in Berlin

Each scenario includes:

- fixed coordinates and address
- default system parameters
- preset comparison variants for the scenario comparison tab
- a shared comparison context so demo variants only change system-specific fields
- deterministic weather coefficients used to generate the same demo-ready outputs every run

## Run The Backend In Demo Mode

From `solar_backend/`:

```bash
DEMO_MODE=true DEMO_DEFAULT_SCENARIO_ID=tel_aviv_rooftop uvicorn app.main:app --reload
```

Notes:

- `DEMO_MODE=true` forces the backend to use bundled weather data for all supported flows.
- `DEMO_DEFAULT_SCENARIO_ID` is optional. Supported values are `tel_aviv_rooftop`, `phoenix_distribution_center`, and `berlin_school_campus`.

## Run The UI In Demo Mode

From the repository root:

```bash
SOLAR_UI_DEMO_MODE=true streamlit run solar_ui/app.py
```

The UI also exposes a sidebar toggle, so you can turn demo mode on without setting the environment variable.

## Recommended Demo Flow

1. Enable demo mode in the sidebar if it is not already on.
2. Pick a bundled scenario from the `Demo Scenario` selector.
3. Click `Run Alpha Forecast` to generate the yearly forecast and daily simulation.
4. Open `Accuracy Backtest` and run the backtest.
5. Open `Scenario Comparison` and click `Load Demo Variants`, then run the comparison.

## Behavior Notes

- In demo mode, map editing is intentionally disabled so the selected scenario stays deterministic.
- Request payloads carry `demo_mode` and `demo_scenario_id` so the backend and UI stay aligned.
- Backend responses expose `data_source=demo` plus the active scenario metadata, and the UI surfaces that state in every major results view.

## When To Use It

Use demo mode for:

- presentations
- graded demonstrations
- screenshots and recordings
- environments with restricted or unreliable internet access
