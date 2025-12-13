# Models Documentation

This document describes the Pydantic models used in the Solar Energy Prediction System API.

## Base Models

### BasePVRequest

The base request model for all photovoltaic (PV) system calculations. Contains common parameters used across different endpoints.

**Fields:**

- `latitude` (float, required): Geographic latitude of the PV system location (-90 to 90)
- `longitude` (float, required): Geographic longitude of the PV system location (-180 to 180)
- `tilt` (float, default: 30.0): Panel tilt angle in degrees (0-90)
- `panel_area` (float, default: 80.0): Total panel area in square meters (m²)
- `panel_efficiency` (float, default: 0.20): Panel efficiency as a decimal (0.0-1.0), e.g., 0.20 = 20%
- `cleanliness` (str, default: "normal"): Panel cleanliness level affecting performance
  - Options: "clean", "normal", "dirty"
- `shading` (str, default: "low"): Shading level affecting the system
  - Options: "none", "low", "medium", "high"
- `ac_capacity_kw` (float | None, optional): AC capacity in kilowatts for inverter sizing
- `gamma` (float, default: 0.004): Temperature coefficient (power loss per °C above 25°C)
- `noct` (float, default: 45.0): Nominal Operating Cell Temperature in degrees Celsius

## Request Models

### SimulationRequest

Inherits from `BasePVRequest` without additional fields. Used for immediate solar panel simulations based on current or provided weather data.

**Endpoint:** `/simulate`

**Purpose:** Calculate instantaneous or short-term solar energy production based on location and panel specifications.

**Example:**
```json
{
  "latitude": 32.08,
  "longitude": 34.78,
  "tilt": 30.0,
  "panel_area": 80.0,
  "panel_efficiency": 0.20,
  "cleanliness": "normal",
  "shading": "low"
}
```

### YearlyForecastRequest

Inherits from `BasePVRequest` with an additional `year` field. Used for yearly solar energy production forecasting using Prophet machine learning model.

**Endpoint:** `/yearly-forecast`

**Additional Fields:**
- `year` (int | None, optional): Target year for forecasting. If not provided, uses current year.

**Purpose:** Generate yearly solar energy production forecasts based on historical data and location parameters. Returns monthly breakdown and total yearly production.

**Example:**
```json
{
  "latitude": 32.08,
  "longitude": 34.78,
  "tilt": 30.0,
  "panel_area": 80.0,
  "panel_efficiency": 0.20,
  "year": 2024,
  "gamma": 0.004,
  "noct": 45.0
}
```

## Usage Notes

### Parameter Guidelines

**Location Parameters:**
- Ensure latitude/longitude coordinates are accurate for best results
- System uses these coordinates to fetch weather data and calculate solar angles

**Panel Parameters:**
- `panel_area`: Total surface area of all panels combined
- `panel_efficiency`: Modern panels typically range from 0.15-0.22 (15%-22%)
- `tilt`: Optimal tilt often equals latitude for fixed installations

**Environmental Factors:**
- `cleanliness`: Accounts for dust, dirt, and debris on panels
- `shading`: Considers nearby obstacles (trees, buildings, etc.)

**Temperature Parameters:**
- `gamma`: Temperature coefficient varies by panel type (typically 0.003-0.005)
- `noct`: Standard is 45°C but varies by manufacturer

### Best Practices

1. **Use realistic values**: Default values are reasonable starting points but adjust based on actual system specifications
2. **Consider local conditions**: Adjust cleanliness and shading based on site-specific factors
3. **Validate coordinates**: Ensure coordinates are within valid ranges and match intended location
4. **Temperature coefficients**: Use manufacturer specifications when available for `gamma` and `noct`

## Model Hierarchy

```
BasePVRequest (base class)
├── SimulationRequest (immediate calculations)
└── YearlyForecastRequest (ML-based forecasting)
```

All models use Pydantic for:
- Automatic data validation
- Type checking
- JSON serialization/deserialization
- Clear error messages for invalid inputs
