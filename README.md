# Solar Energy Estimator

An academic final-project web application for explainable solar-energy estimation:

`React -> FastAPI -> Open-Meteo -> simplified physical PV model -> energy and finance results`

## Implemented capabilities

- Address search and map-based geographic selection
- Configurable panel area, efficiency, tilt, temperature behavior, losses, and AC capacity
- Next-day hourly AC-power estimate from Open-Meteo forecast weather
- Monthly and yearly energy estimate from an archived weather reference year
- Scenario comparison using one shared weather profile
- Flat-tariff value, annual savings, and simple payback

The production model label returned by the API is `simplified_physical_pv_model`. For current or future forecast years, the yearly endpoint reuses the latest complete archive year and reports both the requested and reference years.

## Run with Docker

```bash
docker compose up --build
```

Open <http://127.0.0.1:8000>. No API key is required. Runtime estimates require network access to Open-Meteo; address search and map tiles also require network access.

## Run locally

Backend:

```bash
cd solar_backend
python3 -m venv venv
source venv/bin/activate
pip install -r backend_requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd solar_frontend
npm install
npm run dev
```

Vite proxies API requests to `http://127.0.0.1:8000`. Override it with `VITE_API_PROXY_TARGET` or use `VITE_API_BASE_URL` for direct API calls.

## API

- `POST /simulate` — next-day hourly production and daily value
- `POST /forecast/yearly` — monthly/yearly production and financial summary
- `POST /scenarios/compare` — shared-weather comparison of two or more systems
- `GET /health` — service health

Request fields use these units: irradiance is supplied by Open-Meteo in W/m², panel area is m², AC capacity is kW, hourly energy is kWh, and yearly energy is kWh/year.

## Model boundaries

The project uses a deliberately simplified and transparent model: GHI is adjusted by a latitude/tilt cosine approximation, cell temperature uses NOCT, DC power uses panel area and efficiency, cleanliness/shading/wiring/inverter assumptions form one loss factor, and output is clipped at AC capacity. It is an academic estimator, not a bankable yield study or production-monitoring system.

Finance assumes every generated kWh has the configured flat value. It excludes degradation, maintenance, financing, taxes, export constraints, discounting, and time-of-use tariffs.

## Quality gates

```bash
cd solar_backend
python3 -m pytest -q
python3 -m ruff check .
python3 -m black --check .

cd ../solar_frontend
npm run lint
npm run build

cd ..
docker build -t solar-energy-app .
```
