# Solar Energy Prediction System

Alpha version of a solar energy forecasting project for academic engineering submission.

The system combines:
- A FastAPI backend for weather retrieval, PV simulation, yearly forecasting, scenario comparison, and backtest accuracy analysis.
- A Streamlit frontend for location selection, system configuration, forecast visualization, monetary estimation, and demo-ready what-if flows.

## Alpha Scope

Implemented in this version:
- 24-hour solar production simulation from forecast weather
- Yearly forecast with two paths:
  - `physical`: physics-based PV simulation using archived weather as the baseline profile
  - `ml`: a lightweight trained regression model that forecasts hourly irradiance and temperature from historical weather patterns, then converts that forecast into energy
- Monetary estimation from predicted kWh using a configurable tariff
- Scenario comparison against a baseline system
- Accuracy backtest with monthly and yearly MAPE
- Map-assisted roof area selection in the UI
- Clear backend metadata for fallback behavior, reference years, and ML training years

## Main Endpoints

- `GET /`
- `GET /health`
- `POST /simulate`
- `POST /forecast/yearly`
- `POST /scenarios/compare`
- `POST /evaluation/accuracy`

Swagger is available at `http://127.0.0.1:8000/swagger`.
OpenAPI JSON is available at `http://127.0.0.1:8000/openapi.json`.

## Repository Layout

```text
solar-energy-prediction/
├── solar_backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   ├── routers/
│   │   └── services/
│   ├── backend_requirements.txt
│   └── tests/
├── solar_ui/
│   ├── app.py
│   ├── frontend_requirements.txt
│   └── utils.py
├── architecture/
├── ARCHITECTURE.md
├── IMPLEMENTATION_STATUS.md
├── TESTING_STRATEGY.md
└── README.md
```

## Quick Start

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
cd solar_ui
python3 -m venv venv
source venv/bin/activate
pip install -r frontend_requirements.txt
streamlit run app.py
```

Frontend URL: `http://localhost:8501`

### 3. Docker option

```bash
docker build -t solar-energy-app .
docker run -p 8000:8000 -p 8501:8501 solar-energy-app
```

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
    "electricity_price_per_kwh": 0.17,
    "currency": "USD"
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
    "electricity_price_per_kwh": 0.17,
    "currency": "USD"
  }'
```

### Scenario comparison

```bash
curl -X POST http://127.0.0.1:8000/scenarios/compare \
  -H "Content-Type: application/json" \
  -d '[
    {
      "latitude": 32.08,
      "longitude": 34.78,
      "year": 2026,
      "panel_area": 80.0,
      "panel_efficiency": 0.20,
      "ac_capacity_kw": 15.0,
      "model_type": "physical",
      "electricity_price_per_kwh": 0.17,
      "currency": "USD"
    },
    {
      "latitude": 32.08,
      "longitude": 34.78,
      "year": 2026,
      "panel_area": 96.0,
      "panel_efficiency": 0.20,
      "ac_capacity_kw": 18.0,
      "model_type": "physical",
      "electricity_price_per_kwh": 0.17,
      "currency": "USD"
    }
  ]'
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
    "electricity_price_per_kwh": 0.17,
    "currency": "USD"
  }'
```

## Demo Flow

Recommended Alpha demo:
1. Open the Streamlit UI.
2. Resolve an address and optionally draw a roof rectangle to auto-fill panel area.
3. Run a yearly forecast with `physical` mode.
4. Switch to `ml` mode and rerun to show the alternative forecasting path.
5. Open the Accuracy tab and run the backtest to show monthly/yearly MAPE.
6. Add one or two scenarios with larger panel area or inverter size and compare results.

## Testing

Backend tests:

```bash
cd solar_backend
pytest -q
```

Current backend status: `176 passed, 1 skipped`

The skipped test is the live weather API check, which is skipped when the test environment has no internet access.

## Submission Documents

- `ARCHITECTURE.md`
- `IMPLEMENTATION_STATUS.md`
- `TESTING_STRATEGY.md`
- `architecture/*.puml`

## Notes

- The ML forecast is a real trained baseline model, not a hard-coded placeholder.
- The financial value is an estimate based on the configured tariff assumption. It is intended for demo and comparison use, not billing.
- When the ML forecast cannot be built, the backend falls back to the physical baseline and reports that fallback explicitly in the response.
