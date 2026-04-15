from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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

FRONTEND_DIST_DIR = Path(__file__).resolve().parents[2] / "solar_frontend" / "dist"
FRONTEND_INDEX_FILE = FRONTEND_DIST_DIR / "index.html"
API_PREFIXES = (
    "api",
    "evaluation",
    "forecast",
    "health",
    "openapi.json",
    "redoc",
    "scenarios",
    "simulate",
    "swagger",
)

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


def _resolve_frontend_path(path: str) -> Path | None:
    candidate = (FRONTEND_DIST_DIR / path).resolve()
    try:
        candidate.relative_to(FRONTEND_DIST_DIR.resolve())
    except ValueError:
        return None

    if candidate.is_file():
        return candidate

    return None


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


@app.get("/api", response_model=RootResponse)
def api_root():
    return {"message": "Solar Forecasting Backend is running 🚀"}


@app.get("/", include_in_schema=False)
def root():
    if FRONTEND_INDEX_FILE.is_file():
        return FileResponse(FRONTEND_INDEX_FILE)
    return api_root()


@app.get("/{full_path:path}", include_in_schema=False)
def frontend_routes(full_path: str):
    if not FRONTEND_INDEX_FILE.is_file():
        raise HTTPException(status_code=404, detail="Frontend build is not available.")

    if full_path.startswith(API_PREFIXES):
        raise HTTPException(status_code=404, detail="Not Found")

    frontend_file = _resolve_frontend_path(full_path)
    if frontend_file is not None:
        return FileResponse(frontend_file)

    return FileResponse(FRONTEND_INDEX_FILE)
