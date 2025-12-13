# Services Documentation

This document describes the business logic and utility services in the Solar Energy Prediction System.

## Overview

Services contain the core business logic for weather data retrieval, solar energy calculations, and system performance modeling. They are used by routers to process requests and generate responses.

---

## Weather Services

### 1. Weather Service (`weather_service.py`)

Handles real-time weather forecast retrieval from Open-Meteo API.

#### Functions

##### `get_weather_forecast(lat: float, lon: float, days: int = 1) -> dict | None`

Retrieves hourly weather forecast including solar irradiance and temperature.

**Parameters:**
- `lat`: Latitude coordinate
- `lon`: Longitude coordinate
- `days`: Number of forecast days (default: 1)

**Returns:**
- Dictionary with hourly data including:
  - `shortwave_radiation`: Solar irradiance in W/m²
  - `temperature_2m`: Air temperature at 2 meters in °C
- `None` if request fails

**API Source:** Open-Meteo Forecast API

**Example Response Structure:**
```python
{
    "hourly": {
        "time": ["2024-01-01T00:00", "2024-01-01T01:00", ...],
        "shortwave_radiation": [0, 0, 0, 150, 300, ...],
        "temperature_2m": [15.2, 14.8, 14.5, 16.2, ...]
    }
}
```

**Use Cases:**
- Real-time production simulation
- Short-term forecasting
- Day-ahead planning

---

### 2. Weather Archive Service (`weather_archive_service.py`)

Retrieves historical weather data for long-term analysis and forecasting.

#### Functions

##### `get_year_archive(lat: float, lon: float, year: int) -> pd.DataFrame`

Fetches hourly historical weather data for an entire year.

**Parameters:**
- `lat`: Latitude coordinate
- `lon`: Longitude coordinate
- `year`: Target year for historical data

**Returns:**
- Pandas DataFrame with columns:
  - `time`: Datetime timestamp
  - `irr`: Solar irradiance (W/m²)
  - `temp`: Air temperature (°C)

**API Source:** Open-Meteo Archive API

**Data Range:** Complete hourly data for the specified year (8760 hours)

**Example Usage:**
```python
df = get_year_archive(32.08, 34.78, 2023)
# Returns DataFrame with 8760 rows (365 days × 24 hours)
```

**Use Cases:**
- Yearly forecasting
- Historical performance analysis
- Seasonal pattern detection

---

### 3. Climate Service (`climate_service.py`)

Provides long-term climate normals based on 30-year averages.

#### Functions

##### `get_climate_daily(lat: float, lon: float) -> dict`

Fetches 30-year climate normal data for daily irradiance and temperature averages.

**Parameters:**
- `lat`: Latitude coordinate
- `lon`: Longitude coordinate

**Returns:**
- Dictionary with daily climate normals from 1991-2020

**API Source:** Open-Meteo Climate API

**Use Cases:**
- Long-term planning
- Climate baseline comparison
- Expected production estimation

---

## Simulation Services

### 4. Simulation Service (`simulation_service.py`)

Core PV (photovoltaic) system simulation with detailed physics modeling.

#### Functions

##### `calculate_poa(ghi: float, latitude: float, tilt: float) -> float`

Converts Global Horizontal Irradiance (GHI) to Plane-Of-Array (POA) irradiance.

**Parameters:**
- `ghi`: Global Horizontal Irradiance (W/m²)
- `latitude`: Location latitude
- `tilt`: Panel tilt angle (degrees)

**Returns:**
- POA irradiance accounting for panel angle (W/m²)

**Algorithm:**
- Uses cosine correction based on difference between latitude and tilt
- Optimizes for fixed-tilt systems

---

##### `calculate_cell_temp(poa: float, ambient_temp: float, noct: float) -> float`

Estimates solar cell temperature using NOCT (Nominal Operating Cell Temperature) model.

**Parameters:**
- `poa`: Plane-of-array irradiance (W/m²)
- `ambient_temp`: Ambient air temperature (°C)
- `noct`: Nominal Operating Cell Temperature (°C)

**Returns:**
- Estimated cell temperature (°C)

**Formula:**
```
T_cell = T_ambient + (NOCT - 20°C) / 800 * POA
```

**Why It Matters:**
- Solar panels lose efficiency as temperature increases
- Accurate temperature modeling improves prediction accuracy

---

##### `calculate_dc_power_kw(poa, t_cell, panel_area, efficiency_stc, gamma) -> float`

Calculates DC power output with temperature derating.

**Parameters:**
- `poa`: Plane-of-array irradiance (W/m²)
- `t_cell`: Cell temperature (°C)
- `panel_area`: Total panel area (m²)
- `efficiency_stc`: Panel efficiency at STC (Standard Test Conditions)
- `gamma`: Temperature coefficient (power loss per °C)

**Returns:**
- DC power in kW

**Formula:**
```
thermal_factor = 1 - gamma × (T_cell - 25°C)
DC_power = POA × area × efficiency × thermal_factor / 1000
```

---

##### `apply_system_losses(dc_kw: float, system_loss_factor: float) -> float`

Applies aggregated system losses to DC power.

**Parameters:**
- `dc_kw`: DC power before losses (kW)
- `system_loss_factor`: Multiplier for total losses (0-1)

**Returns:**
- Power after system losses (kW)

**Example:**
- `system_loss_factor = 0.87` means 13% total losses

---

##### `apply_inverter_clipping(ac_kw: float, ac_capacity_kw: Optional[float]) -> float`

Limits AC output to inverter capacity.

**Parameters:**
- `ac_kw`: AC power before clipping (kW)
- `ac_capacity_kw`: Inverter rated capacity (kW), or None for no clipping

**Returns:**
- AC power after clipping (kW)

**Purpose:**
- Prevents over-generation beyond inverter capacity
- Models real-world inverter limitations

---

##### `simulate_production_enhanced(...) -> List[float]`

Full end-to-end PV simulation pipeline.

**Parameters:**
- `irradiance_list`: List of hourly GHI values (W/m²)
- `temp_list`: List of hourly temperatures (°C)
- `latitude`: Location latitude
- `tilt`: Panel tilt angle
- `panel_area`: Total panel area (m²)
- `efficiency`: Panel efficiency at STC
- `gamma`: Temperature coefficient
- `noct`: Nominal Operating Cell Temperature
- `system_loss_factor`: Total system losses multiplier
- `ac_capacity_kw`: Optional inverter capacity for clipping

**Returns:**
- List of hourly AC power outputs (kW)

**Process Flow:**
```
GHI → POA → T_cell → DC Power → System Losses → AC Clipping
```

**Use Cases:**
- Primary simulation engine for all production calculations
- Used by both simulate and yearly forecast endpoints

---

## Loss Calculation Service

### 5. Loss Service (`loss_service.py`)

Calculates system loss factors based on environmental and equipment factors.

#### Functions

##### `get_cleanliness_loss(level: str) -> float`

Returns fractional power loss due to panel cleanliness.

**Parameters:**
- `level`: Cleanliness level ("clean", "normal", "dusty")

**Returns:**
- Loss fraction (0-1)

**Loss Values:**
- `"clean"`: 2% loss
- `"normal"`: 5% loss
- `"dusty"`: 10% loss

---

##### `get_shading_loss(level: str) -> float`

Returns fractional power loss due to shading.

**Parameters:**
- `level`: Shading level ("none", "low", "medium", "high")

**Returns:**
- Loss fraction (0-1)

**Loss Values:**
- `"none"`: 0% loss
- `"low"`: 3% loss
- `"medium"`: 7% loss
- `"high"`: 15% loss

---

##### `compute_system_loss_factor(cleanliness: str, shading: str) -> float`

Computes aggregated system loss factor combining multiple loss sources.

**Parameters:**
- `cleanliness`: Panel cleanliness level
- `shading`: Shading level

**Returns:**
- Combined system loss factor (0-1)

**Components:**
1. **Cleanliness loss**: Based on dust/dirt accumulation
2. **Shading loss**: Based on nearby obstacles
3. **Wiring loss**: Fixed at 2%
4. **Inverter efficiency**: Fixed at 96%

**Formula:**
```
system_factor = (1 - cleanliness_loss) × (1 - shading_loss) × 
                (1 - wiring_loss) × inverter_efficiency
```

**Example:**
```python
compute_system_loss_factor("normal", "low")
# Returns: (1-0.05) × (1-0.03) × (1-0.02) × 0.96 ≈ 0.868
```

**Use Cases:**
- Realistic production modeling
- Account for real-world system degradation
- Performance estimation with environmental factors

---

## Forecasting Services

### 6. Yearly Forecast Service (`yearly_forecast_service.py`)

Processes historical data to generate yearly production forecasts.

#### Functions

##### `compute_yearly_from_real_data(...) -> dict`

Computes yearly production statistics from historical weather data.

**Parameters:**
- `df`: DataFrame with columns `time`, `irr`, `temp`
- `latitude`: Location latitude
- `tilt`: Panel tilt angle
- `panel_area`: Total panel area (m²)
- `efficiency`: Panel efficiency
- `gamma`: Temperature coefficient
- `noct`: Nominal Operating Cell Temperature
- `system_loss_factor`: Total system losses (default: 0.87)

**Returns:**
Dictionary with:
- `monthly_kwh`: List of 12 monthly totals
- `yearly_kwh`: Total annual production (kWh)
- `specific_yield_kwh_per_kwp`: Production per kWp installed
- `avg_daily_kwh`: Average daily production

**Process:**
1. Simulates hourly production for entire year (8760 hours)
2. Aggregates by month
3. Calculates performance metrics
4. Returns comprehensive statistics

**Performance Metrics:**

**Specific Yield:**
```
specific_yield = yearly_kwh / DC_capacity_kWp
```
- Typical range: 800-1800 kWh/kWp depending on location
- Higher values indicate better solar resource or system performance

**Average Daily Production:**
```
avg_daily = yearly_kwh / 365
```

**Use Cases:**
- Annual production estimation
- System sizing
- Financial modeling
- ROI calculations

---

## Service Dependencies

### Dependency Graph

```
weather_service.py ──────┐
weather_archive_service.py ──┐
                           │
                           ├──→ simulation_service.py ──→ yearly_forecast_service.py
                           │           ↑
loss_service.py ────────────┘           │
                                        │
climate_service.py ──────────────────────┘
```

### Integration Points

1. **Routers** call services for business logic
2. **Weather services** provide input data
3. **Loss service** provides correction factors
4. **Simulation service** performs core calculations
5. **Forecast service** aggregates and analyzes results

---

## Best Practices

### Error Handling

1. **API Failures**: Services return `None` or raise exceptions
2. **Data Validation**: Check for required fields in API responses
3. **Graceful Degradation**: Handle missing or invalid data

### Performance

1. **Caching**: Consider caching weather data for repeated queries
2. **Batch Processing**: Process full years efficiently with pandas
3. **Vectorization**: Use numpy/pandas operations for large datasets

### Accuracy

1. **Use Realistic Parameters**: Default values are guidelines, adjust for specific systems
2. **Location Matters**: Solar resource varies significantly by location
3. **Seasonal Variation**: Account for seasonal changes in irradiance and temperature
4. **System Losses**: Real-world systems typically have 10-15% total losses

### Testing

1. **Unit Tests**: Test individual functions with known inputs
2. **Integration Tests**: Test service chains with real API data
3. **Validation**: Compare results against known benchmarks or measurements

---

## Future Enhancements

1. **Additional Weather APIs**: Support for multiple data sources
2. **Machine Learning**: Prophet/LSTM models for improved forecasting
3. **Optimization**: Automated panel angle optimization
4. **Battery Storage**: Integration with energy storage systems
5. **Grid Integration**: Export analysis and grid interaction modeling
6. **Advanced Shading**: Detailed shading analysis with 3D modeling
7. **Degradation Modeling**: Account for panel aging over time
