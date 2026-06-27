from fastapi import APIRouter, HTTPException

from app.exceptions.domain_exceptions import DomainError
from app.exceptions.http_exceptions import exception_to_http_exception
from app.models.requests import YearlyForecastRequest
from app.models.responses import YearlyForecastResponse
from app.exceptions.external_service_exceptions import ExternalServiceError
from app.services.loss_service import compute_system_loss_factor
from app.services.yearly_forecast_service import (
    build_forecast_weather_profile,
    build_yearly_forecast_response,
)

router = APIRouter()


@router.post("", response_model=YearlyForecastResponse)
def yearly(req: YearlyForecastRequest):
    try:
        weather_profile = build_forecast_weather_profile(
            latitude=req.latitude,
            longitude=req.longitude,
            forecast_year=req.year,
            model_type=req.model_type,
            training_years=req.training_years,
        )
        system_loss_factor = compute_system_loss_factor(
            cleanliness=req.cleanliness,
            shading=req.shading,
        )
        return build_yearly_forecast_response(
            weather_profile=weather_profile,
            latitude=req.latitude,
            longitude=req.longitude,
            tilt=req.tilt,
            panel_area=req.panel_area,
            efficiency=req.panel_efficiency,
            gamma=req.gamma,
            noct=req.noct,
            system_loss_factor=system_loss_factor,
            ac_capacity_kw=req.ac_capacity_kw,
            electricity_price_per_kwh=req.electricity_price_per_kwh,
            currency=req.currency,
            system_capex=req.system_capex,
        )
    except ExternalServiceError as exc:
        raise exception_to_http_exception(exc) from exc
    except DomainError as exc:
        raise exception_to_http_exception(exc) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Yearly forecast failed: {exc}",
        ) from exc
