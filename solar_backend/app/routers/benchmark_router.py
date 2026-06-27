from fastapi import APIRouter, HTTPException
import pandas as pd

from app.exceptions.domain_exceptions import DomainError
from app.exceptions.http_exceptions import exception_to_http_exception
from app.models.requests import BenchmarkEvaluationRequest
from app.models.responses import BenchmarkEvaluationResponse
from app.services.benchmark_service import evaluate_forecast_benchmark
from app.exceptions.external_service_exceptions import ExternalServiceError


router = APIRouter()


@router.post("/benchmark", response_model=BenchmarkEvaluationResponse)
def evaluate_benchmark(req: BenchmarkEvaluationRequest):
    evaluation_year = req.year or (pd.Timestamp.now().year - 1)

    try:
        return evaluate_forecast_benchmark(
            latitude=req.latitude,
            longitude=req.longitude,
            year=evaluation_year,
            benchmark_years=req.benchmark_years,
            tilt=req.tilt,
            panel_area=req.panel_area,
            efficiency=req.panel_efficiency,
            cleanliness=req.cleanliness,
            shading=req.shading,
            gamma=req.gamma,
            noct=req.noct,
            ac_capacity_kw=req.ac_capacity_kw,
            training_years=req.training_years,
            demo_mode=req.demo_mode,
            demo_scenario_id=req.demo_scenario_id,
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
            detail=f"Benchmark evaluation failed: {exc}",
        ) from exc
