from pydantic import BaseModel, Field

class BasePVRequest(BaseModel):
    latitude: float
    longitude: float
    tilt: float = 30.0
    panel_area: float = 80.0
    panel_efficiency: float = 0.20
    cleanliness: str = "normal"
    shading: str = "low"
    ac_capacity_kw: float = 15.0
    gamma: float = 0.004
    noct: float = 45.0


class SimulationRequest(BasePVRequest):
    pass


class YearlyForecastRequest(BasePVRequest):
    year: int | None = None



class AccuracyEvaluationRequest(BaseModel):
    latitude: float = Field(
        default=37.0,
        description="System latitude (degrees)",
        examples=[37.0],
    )
    longitude: float = Field(
        default=42.0,
        description="System longitude (degrees)",
        examples=[42.0],
    )
    tilt: float = Field(
        default=45.0,
        description="Panel tilt angle (degrees)",
        examples=[45.0],
    )
    panel_area: float = Field(
        default=80.0,
        description="Total panel area in square meters",
        examples=[80.0],
    )
    panel_efficiency: float = Field(
        default=0.20,
        description="Panel efficiency as a fraction (0–1)",
        examples=[0.20],
    )
    cleanliness: str = Field(
        default="normal",
        description="Panel cleanliness level",
        examples=["normal"],
    )
    shading: str = Field(
        default="low",
        description="Shading level",
        examples=["low"],
    )
    ac_capacity_kw: float = Field(
        default=15.0,
        description="Inverter AC capacity (kW)",
        examples=[15.0],
    )
    gamma: float = Field(
        default=0.004,
        description="Temperature coefficient (1/°C)",
        examples=[0.004],
    )
    noct: float = Field(
        default=45.0,
        description="Nominal Operating Cell Temperature (°C)",
        examples=[45.0],
    )
    year: int | None = Field(
        default=None,
        description="Evaluation year (default: previous year)",
        examples=[2024],
    )