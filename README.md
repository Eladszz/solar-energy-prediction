# Solar Energy Production Prediction System

## Overview
A modular system for predicting solar energy production based on weather data, historical telemetry, and machine-learning models like Prophet and LSTM. The system provides daily/hourly forecasts, anomaly detection, and an interactive Streamlit dashboard.

## System Architecture
```
solar-energy-prediction/
│
├── solar_backend/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── routers/
│       │   ├── forecast_router.py
│       │   ├── simulate_router.py
│       │   └── health_router.py
│       ├── services/
│       │   ├── weather_service.py
│       │   ├── simulation_service.py
│       │   └── forecasting_service.py
│       ├── models/
│       │   ├── common.py
│       │   ├── forecast_models.py
│       │   └── simulate_models.py
│       └── utils/
│           └── http_client.py
│
├── requirements.txt
└── README.md
```

## Backend Components (FastAPI)

### API Endpoints
- **Health Check** (`/health`): Service status verification
- **Forecast** (`/forecast`): Yearly solar energy production forecasting using Prophet
- **Simulate** (`/simulate`): Solar panel simulation based on location and parameters

### Services
- **Weather Service**: Fetch weather data from external APIs
- **Forecasting Service**: Prophet-based yearly forecasting from hourly production data
- **Simulation Service**: Calculate solar energy production based on panel specifications

### Models
- Request/Response models using Pydantic
- Forecast models for Prophet integration
- Simulation models for solar panel calculations

## Running the Application

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the server:
```bash
cd solar_backend
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

## Frontend (Streamlit) - Planned
- Location selection
- Model selection
- Forecast visualization
- Anomaly detection display
- Exportable reports

## Data Flow
```
Weather API → ETL → Feature Engineering → Forecasting → Anomaly Detection → Dashboard
```

## Project Goals
- MAPE < 15%
- Robust fallback when weather data is missing
- <2 minute dashboard load time for 75% of data views
- Full separation of frontend and backend services

## Roadmap
- Week 2: Requirements + Architecture
- Week 4: ETL + EDA
- Week 6: Initial results
- Week 9: Advanced model
- Week 11: Streamlit dashboard
- Week 13: Project book
- Final: Presentation + Prototype

## Tech Stack
- **Backend**: FastAPI, Uvicorn
- **Data Processing**: Pandas, NumPy
- **Forecasting**: Prophet
- **API Integration**: Requests, Pydantic
- **Frontend**: Streamlit (planned)
- **Database**: PostgreSQL / NoSQL (planned)
- **Weather APIs**: OpenWeather/Solcast/PVGIS (planned)

## Security
- All API keys stored in `.env` only
- `.gitignore` prevents committing secrets
- No exposed credentials in repository

## Future Improvements
- Hyperparameter tuning for LSTM
- Multi-horizon forecasting
- Multi-site support
- Docker + Cloud deployment
- MLflow model tracking
- CI/CD pipeline

