from pydantic import BaseModel

class SimulationRequest(BaseModel):
    latitude: float
    longitude: float
    panel_efficiency: float = 0.20
    panel_area: float = 1.6
    tilt: float = 30                 # degrees
    azimuth: float = 180             # south
    gamma: float = 0.004             # temp coefficient
    noct: float = 45                 # Nominal Operating Cell Temp
