from fastapi import APIRouter, HTTPException

from app.services.finance_service import estimate_energy_value
from app.models.requests import SimulationRequest
from app.models.responses import SimulationResponse
from app.services.loss_service import compute_system_loss_factor
from app.services.simulation_service import simulate_production_enhanced
from app.services.weather_service import get_weather_forecast

router = APIRouter()


@router.post("", response_model=SimulationResponse)
def simulate(req: SimulationRequest):
    system_loss_factor = compute_system_loss_factor(
        cleanliness=req.cleanliness,
        shading=req.shading,
    )

    weather = get_weather_forecast(req.latitude, req.longitude, days=1)
    if weather is None or "hourly" not in weather:
        raise HTTPException(
            status_code=502,
            detail="Weather forecast data is currently unavailable for the requested location.",
        )

    irradiance = weather["hourly"].get("shortwave_radiation", [])
    temps = weather["hourly"].get("temperature_2m", [])
    if not irradiance or not temps:
        raise HTTPException(
            status_code=502,
            detail="Weather forecast response did not include the hourly fields required for simulation.",
        )

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
        ac_capacity_kw=req.ac_capacity_kw,
    )

    timezone = weather.get("timezone", "UTC")
    hourly_time = weather.get("hourly", {}).get("time", [])
    daily_kwh = round(sum(ac_power_kw), 1)

    return {
        "location": [req.latitude, req.longitude],
        "system_loss_factor": system_loss_factor,
        "hourly_ac_kw": ac_power_kw,
        "avg_kw": round(sum(ac_power_kw) / len(ac_power_kw), 2),
        "daily_kwh": daily_kwh,
        "estimated_daily_value": estimate_energy_value(
            energy_kwh=daily_kwh,
            electricity_price_per_kwh=req.electricity_price_per_kwh,
        ),
        "financial_assumptions": {
            "electricity_price_per_kwh": round(req.electricity_price_per_kwh, 4),
            "currency": req.currency,
            "valuation_basis": "Estimated daily value from forecasted AC energy.",
        },
        "timezone": timezone,
        "hourly_time": hourly_time,
    }
