from fastapi import APIRouter
from app.models.simulate_models import SimulationRequest
from app.services.weather_service import get_weather_forecast
from app.services.simulation_service import simulate_production_enhanced

router = APIRouter()

@router.post("/")
def simulate(req: SimulationRequest):

    weather = get_weather_forecast(req.latitude, req.longitude, days=1)

    irradiance = weather["hourly"]["shortwave_radiation"]
    temps = weather["hourly"]["temperature_2m"]

    production = simulate_production_enhanced(
        irradiance_list=irradiance,
        temp_list=temps,
        latitude=req.latitude,
        tilt=req.tilt,
        panel_area=req.panel_area,
        efficiency=req.panel_efficiency,
        gamma=req.gamma,
        noct=req.noct
    )

    return {
        "location": (req.latitude, req.longitude),
        "avg_hourly_kw": round(sum(production) / len(production), 4),
        "hourly_production_kw": production
    }
