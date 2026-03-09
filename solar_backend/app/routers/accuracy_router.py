from fastapi import APIRouter, HTTPException
import pandas as pd
from app.models.requests import AccuracyEvaluationRequest
from app.services.accuracy_service import evaluate_yearly_accuracy

router = APIRouter()


@router.post("/accuracy")
def evaluate_accuracy(req: AccuracyEvaluationRequest):

    year = req.year or (pd.Timestamp.now().year - 1)

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
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Accuracy evaluation failed: {exc}",
        ) from exc
