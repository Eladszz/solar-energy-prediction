from fastapi import APIRouter, HTTPException
from typing import List
import logging

from app.models.pv_models import BasePVRequest
from app.services.scenario_comparison_service import compare_yearly_scenarios
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/compare")
def compare_scenarios(
    scenarios: List[BasePVRequest],
):
    """
    Use Case 6.2.2:
    Compare multiple PV system scenarios under identical weather conditions.
    """

    if len(scenarios) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least two scenarios are required for comparison"
        )

    latitude = scenarios[0].latitude
    longitude = scenarios[0].longitude

    # Safety: ensure all scenarios refer to same location
    for s in scenarios:
        if s.latitude != latitude or s.longitude != longitude:
            raise HTTPException(
                status_code=400,
                detail="All scenarios must have the same latitude and longitude"
            )

    try:
        return compare_yearly_scenarios(
            latitude=latitude,
            longitude=longitude,
            scenarios=scenarios,
        )
    except Exception as e:
        logger.error("Scenario comparison error:", e)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
