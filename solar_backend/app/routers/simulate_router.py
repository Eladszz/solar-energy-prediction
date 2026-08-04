import math

from fastapi import APIRouter, HTTPException

from app.services.finance_service import (
    build_financial_assumptions,
    estimate_energy_value,
)
from app.models.requests import SimulationRequest
from app.models.responses import SimulationResponse
from app.exceptions.external_service_exceptions import ExternalServiceError
from app.exceptions.http_exceptions import exception_to_http_exception
from app.services.loss_service import compute_system_loss_factor
from app.services.simulation_service import simulate_production_enhanced
from app.services.weather_service import get_weather_forecast
from app.services.yearly_forecast_service import PRODUCTION_MODEL

router = APIRouter()


@router.post("", response_model=SimulationResponse)
def simulate(req: SimulationRequest):
    try:
        system_loss_factor = compute_system_loss_factor(
            cleanliness=req.cleanliness,
            shading=req.shading,
        )
        weather = get_weather_forecast(
            req.latitude,
            req.longitude,
            days=1,
        )
    except ExternalServiceError as exc:
        raise exception_to_http_exception(exc) from exc

    hourly = weather["hourly"]
    irradiance = []
    for value in hourly["shortwave_radiation"]:
        if value is None:
            irradiance.append(0.0)
            continue
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise HTTPException(
                status_code=502,
                detail="Weather forecast contains invalid irradiance values.",
            )
        irradiance.append(float(value))

    temps = []
    last_temperature: float | None = None
    for value in hourly["temperature_2m"]:
        if value is None:
            if last_temperature is None:
                raise HTTPException(
                    status_code=502,
                    detail="Weather forecast contains unusable temperature values.",
                )
            temps.append(last_temperature)
            continue
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise HTTPException(
                status_code=502,
                detail="Weather forecast contains invalid temperature values.",
            )
        last_temperature = float(value)
        temps.append(last_temperature)

    if not irradiance or not temps:
        raise HTTPException(
            status_code=502,
            detail="Weather forecast provider returned empty hourly fields required for simulation.",
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
        "production_model": PRODUCTION_MODEL,
        "weather_source": "Open-Meteo forecast",
        "system_loss_factor": system_loss_factor,
        "hourly_ac_kw": ac_power_kw,
        "avg_kw": round(sum(ac_power_kw) / len(ac_power_kw), 2),
        "daily_kwh": daily_kwh,
        "estimated_daily_value": estimate_energy_value(
            energy_kwh=daily_kwh,
            electricity_price_per_kwh=req.electricity_price_per_kwh,
        ),
        "financial_assumptions": build_financial_assumptions(
            electricity_price_per_kwh=req.electricity_price_per_kwh,
            currency=req.currency,
            system_capex=req.system_capex,
            valuation_basis="Estimated daily value from forecasted AC energy.",
        ),
        "timezone": timezone,
        "hourly_time": hourly_time,
    }
