# Solar Energy Prediction System

Solar energy forecasting project prepared for academic engineering submission.

The system combines:
- A FastAPI backend for weather retrieval, PV simulation, yearly forecasting, scenario comparison, benchmark evaluation, and backtest accuracy analysis.
- A React frontend for location selection, system configuration, forecast visualization, monetary estimation, benchmark review, and demo-ready what-if flows.

## Alpha Scope

Implemented in this version:
- 24-hour solar production simulation from forecast weather
- Yearly forecast with two paths:
  - `physical`: physics-based PV simulation using archived weather as the baseline profile
  - `ml`: a lightweight trained regression model that forecasts hourly irradiance and temperature from historical weather patterns, then converts that forecast into energy
- Monetary estimation from predicted kWh using a configurable tariff
- Annual savings and simple payback from configurable tariff and CAPEX assumptions
- Scenario comparison against a baseline system using a shared comparison context plus per-scenario system definitions
- Forecast benchmark study comparing `physical`, `ml`, and `naive` baselines on historical periods
- Accuracy backtest with monthly and yearly MAPE
- Map-assisted roof area selection in the UI
- Clear backend metadata for fallback behavior, reference years, ML training years, and benchmark methodology

## Main Endpoints

- `GET /`
- `GET /health`
- `POST /simulate`
- `POST /forecast/yearly`
- `POST /scenarios/compare`
- `POST /evaluation/benchmark`
- `POST /evaluation/accuracy`

Swagger is available at `http://127.0.0.1:8000/swagger`.
OpenAPI JSON is available at `http://127.0.0.1:8000/openapi.json`.

## Repository Layout

```text
solar-energy-prediction/
├── .env.example
├── demo/
│   └── catalog.json
├── solar_backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   ├── routers/
│   │   └── services/
│   ├── backend_requirements.txt
│   └── tests/
├── solar_frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── solar_ui/
│   ├── app.py
│   ├── config.py
│   ├── frontend_requirements.txt
│   └── utils.py
├── architecture/
├── ARCHITECTURE.md
├── DEMO.md
├── Dockerfile
└── README.md
```

## Quick Start

Optional: copy `.env.example` to `.env` and adjust values if you want to change demo mode or frontend/backend URLs.

### 1. Backend setup

```bash
cd solar_backend
python3 -m venv venv
source venv/bin/activate
pip install -r backend_requirements.txt
uvicorn app.main:app --reload
```

Backend URL: `http://127.0.0.1:8000`

### 2. Frontend setup

Open a second terminal:

```bash
cd solar_frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:3000`

The Vite dev server proxies API requests to `http://127.0.0.1:8000` by default, so the React UI can call the backend without extra CORS setup. If your backend runs elsewhere, set `VITE_API_BASE_URL` or `VITE_API_PROXY_TARGET`.

### 3. Docker option

```bash
docker build -t solar-energy-app .
docker run -p 8000:8000 solar-energy-app
```

Docker URL: `http://127.0.0.1:8000`

The container serves the built React UI and the FastAPI API from the same port. In cloud environments, the startup script also honors the platform-provided `PORT` environment variable.

## Example Requests

All examples below use the exact mounted paths exposed by the backend. No trailing slash is required.

### Yearly forecast

```bash
curl -X POST http://127.0.0.1:8000/forecast/yearly \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 32.08,
    "longitude": 34.78,
    "year": 2026,
    "tilt": 30,
    "panel_area": 80.0,
    "panel_efficiency": 0.20,
    "cleanliness": "normal",
    "shading": "low",
    "ac_capacity_kw": 15.0,
    "model_type": "ml",
    "training_years": 3,
    "electricity_price_per_kwh": 0.48,
    "currency": "ILS",
    "system_capex": 60000.0
  }'
```

### Daily simulation

```bash
curl -X POST http://127.0.0.1:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 32.08,
    "longitude": 34.78,
    "panel_area": 80.0,
    "panel_efficiency": 0.20,
    "ac_capacity_kw": 15.0,
    "electricity_price_per_kwh": 0.48,
    "currency": "ILS",
    "system_capex": 60000.0
  }'
```

### Scenario comparison

Scenario comparison now uses one shared `context` object for weather/model/tariff settings, plus a `scenarios` array that contains only scenario-specific system fields.

```bash
curl -X POST http://127.0.0.1:8000/scenarios/compare \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "latitude": 32.08,
      "longitude": 34.78,
      "year": 2026,
      "model_type": "physical",
      "electricity_price_per_kwh": 0.48,
      "currency": "ILS"
    },
    "scenarios": [
      {
        "name": "Base System",
        "panel_area": 80.0,
        "panel_efficiency": 0.20,
        "ac_capacity_kw": 15.0,
        "tilt": 30.0,
        "cleanliness": "normal",
        "shading": "low",
        "gamma": 0.004,
        "noct": 45.0,
        "system_capex": 60000.0
      },
      {
        "name": "Expanded Array",
        "panel_area": 96.0,
        "panel_efficiency": 0.20,
        "ac_capacity_kw": 18.0,
        "tilt": 30.0,
        "cleanliness": "clean",
        "shading": "none",
        "gamma": 0.004,
        "noct": 45.0,
        "system_capex": 30000.0
      }
    ]
  }'
```

### Accuracy backtest

```bash
curl -X POST http://127.0.0.1:8000/evaluation/accuracy \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 32.08,
    "longitude": 34.78,
    "year": 2025,
    "tilt": 30,
    "panel_area": 80.0,
    "panel_efficiency": 0.20,
    "cleanliness": "normal",
    "shading": "low",
    "ac_capacity_kw": 15.0,
    "model_type": "ml",
    "training_years": 3,
    "electricity_price_per_kwh": 0.48,
    "currency": "ILS",
    "system_capex": 60000.0
  }'
```

### Benchmark evaluation

Benchmark evaluation uses the same PV conversion stack for all approaches and compares:
- `physical`: prior-year archived weather baseline
- `ml`: trained weather-profile forecast
- `naive`: simple historical climatology baseline

The benchmark reference is a transparent production proxy built by replaying archived actual weather through the shared PV simulation layer. That keeps the comparison deterministic and academically honest even though this repository does not ship plant telemetry.

```bash
curl -X POST http://127.0.0.1:8000/evaluation/benchmark \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 32.08,
    "longitude": 34.78,
    "year": 2025,
    "benchmark_years": 3,
    "tilt": 30,
    "panel_area": 80.0,
    "panel_efficiency": 0.20,
    "cleanliness": "normal",
    "shading": "low",
    "ac_capacity_kw": 15.0,
    "gamma": 0.004,
    "noct": 45.0,
    "training_years": 3
  }'
```

## Demo Flow

Recommended Alpha demo:
1. Open the React UI.
2. Resolve an address and optionally draw a roof rectangle to auto-fill panel area.
3. Run a yearly forecast with `physical` mode.
4. Switch to `ml` mode and rerun to show the alternative forecasting path.
5. Open the Benchmark Study tab to compare the physical, ML, and naive baselines on historical periods.
6. Open the Accuracy tab and run the backtest to show monthly/yearly MAPE for the currently selected forecast path.
7. Add one or two system variants and compare them under the same shared weather/model/tariff context.

## Testing

Backend tests:

```bash
cd solar_backend
pytest -q
```

The automated suite covers request validation, route contracts, scenario comparison semantics, benchmark aggregation, and core forecast services. Live-provider checks may be skipped automatically when internet access is unavailable.

## Submission Documents

- `ARCHITECTURE.md`
- `DEMO.md`
- `architecture/*.puml`

## Notes

- The ML forecast is a real trained baseline model, not a hard-coded placeholder.
- Financial outputs assume each kWh offsets or earns the configured flat tariff. Annual savings are treated as equal to yearly estimated value.
- Simple payback is `system_capex / annual_savings`. It is intentionally simple and ignores financing, taxes, maintenance, degradation, export limits, and time-of-use pricing.
- When the ML forecast cannot be built, the backend falls back to the physical baseline and reports that fallback explicitly in the response.
