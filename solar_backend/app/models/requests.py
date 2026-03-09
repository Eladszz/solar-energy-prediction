from typing import Literal

from pydantic import BaseModel, Field

ModelType = Literal["physical", "ml"]


class BasePVRequest(BaseModel):
    latitude: float
    longitude: float
    year: int | None = None
    tilt: float = 30.0
    panel_area: float = 80.0
    panel_efficiency: float = 0.20
    cleanliness: str = "normal"
    shading: str = "low"
    ac_capacity_kw: float = 15.0
    gamma: float = 0.004
    noct: float = 45.0
    model_type: ModelType = "physical"
    electricity_price_per_kwh: float = Field(default=0.17, ge=0.0)
    currency: str = "USD"
    training_years: int = Field(default=3, ge=1, le=10)


class SimulationRequest(BasePVRequest):
    pass


class YearlyForecastRequest(BasePVRequest):
    pass


class AccuracyEvaluationRequest(BasePVRequest):
    pass
