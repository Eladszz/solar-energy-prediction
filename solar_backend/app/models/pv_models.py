from pydantic import BaseModel

class BasePVRequest(BaseModel):
    latitude: float
    longitude: float
    tilt: float = 30.0
    panel_area: float = 80.0
    panel_efficiency: float = 0.20
    cleanliness: str = "normal"
    shading: str = "low"
    ac_capacity_kw: float | None = None
    gamma: float = 0.004
    noct: float = 45.0


class SimulationRequest(BasePVRequest):
    pass


class YearlyForecastRequest(BasePVRequest):
    year: int | None = None