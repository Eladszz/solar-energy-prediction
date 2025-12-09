from fastapi import APIRouter
from app.models.forecast_models import YearlyForecastRequest
from app.services.yearly_real_data_service import get_year_archive
from app.services.yearly_production_from_realdata import compute_yearly_from_real_data
import pandas as pd
router = APIRouter()

@router.post("/")
def yearly(req: YearlyForecastRequest):

    df = get_year_archive(req.latitude, req.longitude, pd.Timestamp.now().year - 1)

    result = compute_yearly_from_real_data(
        df=df,
        latitude=req.latitude,
        tilt=req.tilt,
        panel_area=req.panel_area,
        efficiency=req.panel_efficiency,
        gamma=req.gamma,
        noct=req.noct
    )

    return {
        "location": (req.latitude, req.longitude),
        "monthly_kwh": result["monthly_kwh"],
        "yearly_kwh": result["yearly_kwh"]
    }
