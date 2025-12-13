# Solar Energy Production Prediction System

## Overview
A FastAPI-based system for predicting solar energy production using real-time weather forecasts and historical climate data. The system provides hourly simulations and yearly forecasts with detailed physics-based PV modeling, including temperature effects, system losses, and inverter clipping.

## System Architecture
```
solar-energy-prediction/
│
├── solar_backend/
│   └── app/
│       ├── main.py              # FastAPI application entry point
│       ├── config.py            # Configuration and constants
│       ├── routers/
│       │   ├── health_router.py         # Health check endpoint
│       │   ├── simulate_router.py       # 24h production simulation
│       │   ├── yearly_forecast_router.py # Yearly forecasting
│       │   └── routers.md               # Router documentation
│       ├── services/
│       │   ├── weather_service.py           # Real-time weather data
│       │   ├── weather_archive_service.py   # Historical weather data
│       │   ├── climate_service.py           # Climate normals
│       │   ├── simulation_service.py        # PV physics modeling
│       │   ├── loss_service.py              # System loss calculations
│       │   ├── yearly_forecast_service.py   # Yearly aggregation
│       │   └── services.md                  # Service documentation
│       ├── models/
│       │   ├── pv_models.py    # Pydantic request models
│       │   └── models.md       # Model documentation
│       └── utils/
│           └── http_client.py  # HTTP utilities
│
├── requirements.txt    # Python dependencies
├── run.sh             # Startup script
└── README.md          # This file
```

## API Endpoints

### 1. Health Check
**GET** `/health`

Verify API service status.

**Response:**
```json
{"status": "ok"}
```

### 2. Simulate Production
**POST** `/simulate`

Simulate 24-hour solar energy production based on weather forecast.

**Request Body:**
```json
{
  "latitude": 32.08,
  "longitude": 34.78,
  "tilt": 30.0,
  "panel_area": 80.0,
  "panel_efficiency": 0.20,
  "cleanliness": "normal",
  "shading": "low",
  "gamma": 0.004,
  "noct": 45.0
}
```

**Response:**
```json
{
  "location": [32.08, 34.78],
  "system_loss_factor": 0.868,
  "hourly_ac_kw": [0.0, 0.0, ..., 15.2, ..., 0.0],
  "avg_kw": 8.5
}
```

### 3. Yearly Forecast
**POST** `/yearly-forecast`

Generate yearly production forecast using historical weather data.

**Request Body:**
```json
{
  "latitude": 32.08,
  "longitude": 34.78,
  "tilt": 30.0,
  "panel_area": 80.0,
  "panel_efficiency": 0.20,
  "year": 2024
}
```

**Response:**
```json
{
  "location": [32.08, 34.78],
  "monthly_kwh": [450.2, 520.5, ..., 430.1],
  "yearly_kwh": 6850.5,
  "specific_yield_kwh_per_kwp": 1250.3,
  "avg_daily_kwh": 18.8
}
```

## Key Features

### Physics-Based PV Modeling
- **POA Calculation**: Converts GHI to plane-of-array irradiance
- **Temperature Modeling**: NOCT-based cell temperature estimation
- **Thermal Derating**: Accounts for efficiency loss at high temperatures
- **System Losses**: Cleanliness, shading, wiring, and inverter efficiency
- **Inverter Clipping**: Models inverter capacity limitations

### Weather Data Integration
- **Real-time Forecasts**: Open-Meteo API for 24h predictions
- **Historical Archives**: Full year hourly data for forecasting
- **Climate Normals**: 30-year averages for baseline comparisons

### Comprehensive Documentation
- **[Models Documentation](solar_backend/app/models/models.md)**: Detailed model schemas
- **[Routers Documentation](solar_backend/app/routers/routers.md)**: API endpoint specifications
- **[Services Documentation](solar_backend/app/services/services.md)**: Business logic details

## Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd solar-energy-prediction
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

**Option 1: Using the startup script**
```bash
./run.sh
```

**Option 2: Manual start**
```bash
cd solar_backend
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

### Interactive API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Testing the API

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Simulate Production:**
```bash
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 32.08,
    "longitude": 34.78,
    "panel_area": 80.0,
    "panel_efficiency": 0.20
  }'
```

**Yearly Forecast:**
```bash
curl -X POST http://localhost:8000/yearly-forecast \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 32.08,
    "longitude": 34.78,
    "tilt": 30.0,
    "panel_area": 80.0,
    "panel_efficiency": 0.20
  }'
```

## Data Flow

### Simulation Flow (24h)
```
User Request → Weather Forecast API → POA Calculation → 
Cell Temperature → DC Power → System Losses → 
Inverter Clipping → Hourly AC Power Output
```

### Yearly Forecast Flow
```
User Request → Historical Weather Archive → Hourly Simulation (8760h) → 
Monthly Aggregation → Performance Metrics → Yearly Statistics
```

## Technical Details

### PV Modeling Approach

**1. Irradiance Conversion**
- Converts Global Horizontal Irradiance (GHI) to Plane-Of-Array (POA)
- Uses cosine correction based on latitude and tilt angle

**2. Temperature Effects**
- NOCT model for cell temperature estimation
- Temperature coefficient (gamma) for thermal derating
- Typical efficiency loss: 0.4% per °C above 25°C

**3. System Losses**
- **Cleanliness**: 2-10% (clean to dusty)
- **Shading**: 0-15% (none to high)
- **Wiring**: 2% fixed
- **Inverter**: 96% efficiency
- **Total**: Typically 13-20% combined losses

**4. Performance Metrics**
- **Specific Yield**: kWh produced per kWp installed
- **Capacity Factor**: Actual vs. theoretical maximum production
- **Average Daily Production**: Total yearly kWh / 365

### API Design Principles

- **RESTful Architecture**: Standard HTTP methods and status codes
- **Type Safety**: Pydantic models for validation
- **Error Handling**: Graceful degradation with informative messages
- **Documentation**: Auto-generated OpenAPI/Swagger docs
- **Modularity**: Separation of concerns (routers → services → utilities)

## Tech Stack

### Core Framework
- **FastAPI**: Modern, fast web framework with automatic API documentation
- **Uvicorn**: Lightning-fast ASGI server
- **Pydantic**: Data validation and settings management

### Data Processing
- **Pandas**: Time series data manipulation and aggregation
- **NumPy**: Numerical computations

### External APIs
- **Open-Meteo**: Free weather forecast and historical archive data
  - Forecast API: Real-time 24h predictions
  - Archive API: Historical hourly data
  - Climate API: 30-year climate normals

### Future Integrations
- **Prophet**: Time series forecasting with seasonality
- **LSTM**: Deep learning for complex patterns
- **Streamlit**: Interactive web dashboard
- **PostgreSQL**: Persistent data storage

## Project Structure

### Configuration
- `config.py`: Application settings and API URLs
- `requirements.txt`: Python package dependencies
- `.vscode/settings.json`: VS Code Python path configuration

### Core Modules
- **Routers**: API endpoint definitions and request handling
- **Services**: Business logic and external API integration
- **Models**: Pydantic schemas for request/response validation
- **Utils**: Shared utilities and helper functions

### Documentation
- Inline code documentation and docstrings
- Markdown files for comprehensive guides
- Auto-generated API docs via FastAPI

## Future Enhancements

### Near-term
- [ ] Prophet integration for ML-based forecasting
- [ ] Streamlit dashboard for visualization
- [ ] Caching layer for repeated queries
- [ ] Unit and integration tests

### Medium-term
- [ ] Multi-site comparison and aggregation
- [ ] Battery storage integration
- [ ] Advanced shading analysis with 3D modeling
- [ ] Export analysis and grid interaction

### Long-term
- [ ] LSTM models for complex pattern recognition
- [ ] Docker containerization
- [ ] Cloud deployment (AWS/GCP/Azure)
- [ ] CI/CD pipeline with automated testing
- [ ] Real-time monitoring dashboard
- [ ] Mobile application

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request


## Contact

Eladszt@gmail.com

---

**Note**: This system uses free Open-Meteo APIs which require no authentication. For production use, consider API rate limits and caching strategies.

