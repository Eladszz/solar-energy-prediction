from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import config
from app.models.responses import RootResponse
from app.routers import (
    benchmark_router,
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


def _parse_cors_allow_origins(raw_value: str) -> list[str]:
    origins = [origin.strip() for origin in raw_value.split(",") if origin.strip()]
    return origins or ["http://localhost:3000", "http://127.0.0.1:3000"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_allow_origins(config.CORS_ALLOW_ORIGINS),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
app.include_router(
    benchmark_router.router, prefix="/evaluation", tags=["Benchmark Evaluation"]
)


@app.get("/", response_model=RootResponse)
def root():
    return {"message": "Solar Forecasting Backend is running 🚀"}
