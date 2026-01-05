from fastapi import APIRouter
from app.models.pv_models import SimulationRequest
from app.services.weather_service import get_weather_forecast
from app.services.simulation_service import simulate_production_enhanced
from app.services.loss_service import compute_system_loss_factor

router = APIRouter()

@router.post("/")
def simulate(req: SimulationRequest):

    system_loss_factor = compute_system_loss_factor(
        cleanliness=req.cleanliness,
        shading=req.shading
    )

    weather = get_weather_forecast(req.latitude, req.longitude, days=1)
    if weather is None:
        raise ValueError("Failed to retrieve weather forecast")

    irradiance = weather["hourly"]["shortwave_radiation"]
    temps = weather["hourly"]["temperature_2m"]

    ac_power_kw = simulate_production_enhanced(
        irradiance_list=irradiance,
        temp_list=temps,
        latitude=req.latitude,
        tilt=req.tilt,
        panel_area=req.panel_area,
        efficiency=req.panel_efficiency,
        gamma=req.gamma,
        noct=req.noct,
        system_loss_factor=system_loss_factor,
        ac_capacity_kw=req.ac_capacity_kw
    )

    # Extract timezone and time information from weather data
    timezone = weather.get("timezone", "UTC")
    hourly_time = weather.get("hourly", {}).get("time", [])

    return {
        "location": [req.latitude, req.longitude],
        "system_loss_factor": system_loss_factor,
        "hourly_ac_kw": ac_power_kw,
        "avg_kw": sum(ac_power_kw) / len(ac_power_kw),
        "timezone": timezone,
        "hourly_time": hourly_time
    }
