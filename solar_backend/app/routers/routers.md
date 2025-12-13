# Routers Documentation

This document describes the API routers (endpoints) in the Solar Energy Prediction System.

## Overview

The application uses FastAPI's APIRouter to organize endpoints into logical groups. Each router handles a specific aspect of solar energy prediction and system health monitoring.

## Available Routers

### 1. Health Router

**File:** `health_router.py`  
**Prefix:** `/health`  
**Tags:** `["Health"]`

#### Endpoints

##### GET `/health`

Health check endpoint to verify that the API service is running.

**Response:**
```json
{
  "status": "ok"
}
```

**Use Case:** 
- Service monitoring
- Load balancer health checks
- Deployment verification

---

### 2. Simulate Router

**File:** `simulate_router.py`  
**Prefix:** `/simulate`  
**Tags:** Default

#### Endpoints

##### POST `/`

Simulate real-time solar energy production for the next 24 hours based on weather forecast data.

**Request Body:** `SimulationRequest`

**Required Fields:**
- `latitude`: Geographic latitude
- `longitude`: Geographic longitude

**Optional Fields (with defaults):**
- `tilt`: Panel tilt angle (default: 30.0°)
- `panel_area`: Total panel area (default: 80.0 m²)
- `panel_efficiency`: Panel efficiency (default: 0.20 = 20%)
- `cleanliness`: Panel cleanliness ("clean", "normal", "dirty")
- `shading`: Shading level ("none", "low", "medium", "high")
- `ac_capacity_kw`: AC inverter capacity in kW
- `gamma`: Temperature coefficient (default: 0.004)
- `noct`: Nominal Operating Cell Temperature (default: 45.0°C)

**Process:**
1. Calculate system loss factor based on cleanliness and shading
2. Fetch 24-hour weather forecast (irradiance and temperature)
3. Simulate hourly AC power production with temperature effects
4. Apply system losses and inverter clipping if specified

**Response:**
```json
{
  "location": [32.08, 34.78],
  "system_loss_factor": 0.95,
  "hourly_ac_kw": [0.0, 0.0, 0.0, ..., 15.2, ..., 0.0],
  "avg_kw": 8.5
}
```

**Use Case:**
- Real-time production estimation
- Day-ahead planning
- System performance validation

---

### 3. Yearly Forecast Router

**File:** `yearly_forecast_router.py`  
**Prefix:** `/yearly-forecast`  
**Tags:** Default

#### Endpoints

##### POST `/`

Generate yearly solar energy production forecast using historical weather data and Prophet machine learning model.

**Request Body:** `YearlyForecastRequest`

**Required Fields:**
- `latitude`: Geographic latitude
- `longitude`: Geographic longitude

**Optional Fields (with defaults):**
- Same as `SimulationRequest` plus:
- `year`: Target year for forecast (default: current year)

**Process:**
1. Retrieve historical weather archive data for the previous year
2. Calculate system loss factor from cleanliness and shading
3. Simulate production for each hour of the year
4. Aggregate results by month and calculate yearly totals
5. Compute performance metrics (specific yield, daily average)

**Response:**
```json
{
  "location": [32.08, 34.78],
  "monthly_kwh": {
    "1": 450.2,
    "2": 520.5,
    "3": 680.3,
    ...
    "12": 430.1
  },
  "yearly_kwh": 6850.5,
  "specific_yield_kwh_per_kwp": 1250.3,
  "avg_daily_kwh": 18.8
}
```

**Response Fields:**
- `monthly_kwh`: Dictionary mapping month number (1-12) to total kWh produced
- `yearly_kwh`: Total energy production for the year
- `specific_yield_kwh_per_kwp`: Energy production per kW of installed capacity
- `avg_daily_kwh`: Average daily energy production

**Use Case:**
- Annual production estimation
- System sizing and ROI calculations
- Performance benchmarking
- Financial modeling

---

## Router Registration

All routers are registered in the main application (`main.py`) with appropriate prefixes:

```python
from app.routers import health_router, simulate_router, yearly_forecast_router

app.include_router(health_router.router)
app.include_router(simulate_router.router, prefix="/simulate", tags=["Simulation"])
app.include_router(yearly_forecast_router.router, prefix="/yearly-forecast", tags=["Forecast"])
```

## Common Response Patterns

### Success Response
All endpoints return JSON with relevant data fields.

### Error Response
FastAPI automatically generates error responses:

```json
{
  "detail": "Error message description"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `422`: Validation Error (invalid request body)
- `500`: Internal Server Error

## API Testing

### Example cURL Requests

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
    "panel_efficiency": 0.20,
    "year": 2024
  }'
```

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

These interfaces allow you to:
- Explore all endpoints
- View request/response schemas
- Test API calls directly in the browser
- See example values and validation rules

## Best Practices

1. **Use appropriate endpoint:** 
   - `/simulate` for short-term (24h) forecasts
   - `/yearly-forecast` for long-term annual predictions

2. **Validate coordinates:**
   - Ensure latitude is between -90 and 90
   - Ensure longitude is between -180 and 180

3. **Adjust parameters:**
   - Use realistic panel specifications for accurate results
   - Consider local environmental factors (cleanliness, shading)

4. **Error handling:**
   - Always check for error responses
   - Handle network failures gracefully
   - Validate input data before sending requests

5. **Performance considerations:**
   - Yearly forecasts are computation-intensive
   - Consider caching results for repeated queries
   - Use simulate endpoint for frequent updates
