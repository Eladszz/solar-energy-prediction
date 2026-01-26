from fastapi import APIRouter
import pandas as pd
from app.models.requests import AccuracyEvaluationRequest
from app.services.accuracy_service import evaluate_yearly_accuracy

router = APIRouter()


@router.post("/accuracy")
def evaluate_accuracy(req: AccuracyEvaluationRequest):

    year = req.year or (pd.Timestamp.now().year - 1)

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
    )
