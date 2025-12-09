# Solar Energy Production Prediction System

## Overview
A modular system for predicting solar energy production based on weather data, historical telemetry, and machine-learning models like Prophet and LSTM. The system provides daily/hourly forecasts, anomaly detection, and an interactive Streamlit dashboard.

## System Architecture
```
project-root/
│
├── backend/
|   main.py
|   services/
|       weather_service.py
|       simulation_service.py
|       forecasting_service.py
|   models/
|       request_models.py
|       response_models.py
│
├── frontend/
│   └── streamlit_app/
│
├── config/
├── docs/
├── tests/
└── README.md
```

## Backend Components
### Data Ingestion
- Weather API fetch (OpenWeather/Solcast/PVGIS)
- CSV import
- DB integration

### Data Processing & EDA
- Data cleaning
- Feature engineering
- Exploratory data analysis

### Forecasting Models
- Prophet
- LSTM
- XGBoost
Unified interface example:
```python
model = ModelFactory.get("prophet")
forecast = model.predict(data)
```

### Anomaly Detection
- Identifying deviations in expected production

### Storage Layer
- SQL DB for users/auth
- NoSQL DB for logs, predictions, runtime data

## Frontend (Streamlit)
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
- Python, Pandas, Numpy
- Scikit-learn, Prophet, TensorFlow/PyTorch
- Plotly, Streamlit
- PostgreSQL / NoSQL
- Weather APIs

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

