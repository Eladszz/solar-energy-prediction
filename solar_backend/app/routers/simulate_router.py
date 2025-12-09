from fastapi import APIRouter
from app.models.simulate_models import SimulationRequest
from app.services.weather_service import get_weather_forecast
from app.services.simulation_service import simulate_production

router = APIRouter()

@router.post("/")
def simulate(req: SimulationRequest):

    weather = get_weather_forecast(req.latitude, req.longitude, days=1)
    irradiance = weather["hourly"]["shortwave_radiation"]

    production = simulate_production(
        irradiance_list=irradiance,
        panel_efficiency=req.panel_efficiency,
        panel_area=req.panel_area
    )

    return {
        "location": (req.latitude, req.longitude),
        "hourly_production_kw": production
    }
