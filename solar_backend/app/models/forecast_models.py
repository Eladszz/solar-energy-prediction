from pydantic import BaseModel
from typing import List

class ForecastRequest(BaseModel):
    hourly_production: List[float]


class YearlyForecastRequest(BaseModel):
    latitude: float
    longitude: float
    tilt: float = 30
    panel_area: float = 1.6
    panel_efficiency: float = 0.20
    gamma: float = 0.004
    noct: float = 45