from fastapi import APIRouter
from app.models.simulate_models import YearlyForecastRequest
from app.services.yearly_real_data_service import get_year_archive
from app.services.yearly_production_from_realdata import compute_yearly_from_real_data
from app.services.loss_service import compute_system_loss_factor

import pandas as pd
router = APIRouter()

@router.post("/")
def yearly(req: YearlyForecastRequest):

    df = get_year_archive(req.latitude, req.longitude, pd.Timestamp.now().year - 1)
    system_loss_factor = compute_system_loss_factor(cleanliness=req.cleanliness,shading=req.shading)
    result = compute_yearly_from_real_data(
        df=df,
        latitude=req.latitude,
        tilt=req.tilt,
        panel_area=req.panel_area,
        efficiency=req.panel_efficiency,
        gamma=req.gamma,
        noct=req.noct,
        system_loss_factor=system_loss_factor
    )

    return {
        "location": (req.latitude, req.longitude),
        "monthly_kwh": result["monthly_kwh"],

        "yearly_kwh": result["yearly_kwh"],
        "specific_yield_kwh_per_kwp": result["specific_yield_kwh_per_kwp"],
        "avg_daily_kwh": result["avg_daily_kwh"]
    }
