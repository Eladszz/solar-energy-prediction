from pydantic import BaseModel

class SimulationRequest(BaseModel):
    latitude: float
    longitude: float
    panel_efficiency: float = 0.20
    panel_area: float = 1.6
