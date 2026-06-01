from fastapi import APIRouter, HTTPException
import pandas as pd
from app.models.requests import AccuracyEvaluationRequest
from app.models.responses import AccuracyEvaluationResponse
from app.services.external_service import (
    ExternalServiceError,
    external_service_to_http_exception,
)
from app.services.accuracy_service import evaluate_yearly_accuracy

router = APIRouter()


@router.post("/accuracy", response_model=AccuracyEvaluationResponse)
def evaluate_accuracy(req: AccuracyEvaluationRequest):

    last_complete_year = pd.Timestamp.now().year - 1
    year = req.year or last_complete_year
    if year > last_complete_year:
        raise HTTPException(
            status_code=422,
            detail=f"Accuracy evaluation requires a completed year. Latest available year is {last_complete_year}.",
        )

    try:
        return evaluate_yearly_accuracy(
            latitude=req.latitude,
            longitude=req.longitude,
            year=year,
            tilt=req.tilt,
            panel_area=req.panel_area,
            efficiency=req.panel_efficiency,
            cleanliness=req.cleanliness,
            shading=req.shading,
            gamma=req.gamma,
            noct=req.noct,
            ac_capacity_kw=req.ac_capacity_kw,
            model_type=req.model_type,
            training_years=req.training_years,
            electricity_price_per_kwh=req.electricity_price_per_kwh,
            currency=req.currency,
            system_capex=req.system_capex,
            demo_mode=req.demo_mode,
            demo_scenario_id=req.demo_scenario_id,
        )
    except ExternalServiceError as exc:
        raise external_service_to_http_exception(exc) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Accuracy evaluation failed: {exc}",
        ) from exc
