from fastapi import FastAPI
from app.routers import (
    health_router,
    simulate_router,
    yearly_forecast_router,
    scenario_comparison_router,
    accuracy_router,
)
from loguru import logger
from app.logging_conf import configure_logging

app = FastAPI(
    title="Solar Energy Forecasting API",
    version="0.2.0",
    description="Backend for the Solar Production Prediction Final Project",
    docs_url="/swagger",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

configure_logging()
logger.info("Logging is configured.")
# Routers
app.include_router(health_router.router)
app.include_router(simulate_router.router, prefix="/simulate", tags=["Day Simulation"])
app.include_router(
    yearly_forecast_router.router, prefix="/forecast/yearly", tags=["Yearly Forecast"]
)
app.include_router(
    scenario_comparison_router.router, prefix="/scenarios", tags=["Scenario Comparison"]
)
app.include_router(
    accuracy_router.router, prefix="/evaluation", tags=["Accuracy Evaluation"]
)


@app.get("/")
def root():
    return {"message": "Solar Forecasting Backend is running 🚀"}
