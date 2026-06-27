import logging

from fastapi import APIRouter, HTTPException

from app.models.requests import ScenarioComparisonRequest
from app.models.responses import ScenarioComparisonResponse
from app.exceptions.external_service_exceptions import (
    ExternalServiceError,
    external_service_to_http_exception,
)
from app.services.scenario_comparison_service import compare_yearly_scenarios

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/compare", response_model=ScenarioComparisonResponse)
def compare_scenarios(
    req: ScenarioComparisonRequest,
):
    """
    Use Case 6.2.2:
    Compare multiple PV system scenarios under identical weather conditions.
    """

    try:
        return compare_yearly_scenarios(
            context=req.context,
            scenarios=req.scenarios,
        )
    except ExternalServiceError as exc:
        raise external_service_to_http_exception(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as e:
        logger.exception("Scenario comparison error")
        raise HTTPException(status_code=500, detail=str(e))
