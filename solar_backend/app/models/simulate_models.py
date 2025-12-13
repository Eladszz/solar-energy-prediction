from pydantic import BaseModel

class SimulationRequest(BaseModel):
    latitude: float
    longitude: float
    tilt: float = 30
    panel_area: float = 1.6
    panel_efficiency: float = 0.20

    # losses (simple for user)
    cleanliness: str = "normal"   # clean / normal / dusty
    shading: str = "low"          # none / low / medium / high

    # inverter
    ac_capacity_kw: float | None = None

    # thermal
    gamma: float = 0.004
    noct: float = 45
