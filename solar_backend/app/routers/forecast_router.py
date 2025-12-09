from fastapi import APIRouter
from app.models.forecast_models import ForecastRequest
from app.services.forecasting_service import simple_yearly_forecast

router = APIRouter()

@router.post("/")
def forecast(req: ForecastRequest):
    result = simple_yearly_forecast(req.hourly_production)
    return result
