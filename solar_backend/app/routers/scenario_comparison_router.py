import logging
from typing import List

from fastapi import APIRouter, HTTPException

from app.models.requests import BasePVRequest
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
            status_code=400, detail="At least two scenarios are required for comparison"
        )

    latitude = scenarios[0].latitude
    longitude = scenarios[0].longitude

    # Safety: ensure all scenarios refer to same location
    for s in scenarios:
        if s.latitude != latitude or s.longitude != longitude:
            raise HTTPException(
                status_code=400,
                detail="All scenarios must have the same latitude and longitude",
            )
        if s.model_type != scenarios[0].model_type:
            raise HTTPException(
                status_code=400,
                detail="All scenarios must use the same forecast model type for a fair comparison.",
            )
        if s.currency != scenarios[0].currency:
            raise HTTPException(
                status_code=400,
                detail="All scenarios must use the same currency for financial comparison.",
            )
        if s.electricity_price_per_kwh != scenarios[0].electricity_price_per_kwh:
            raise HTTPException(
                status_code=400,
                detail="All scenarios must use the same tariff assumption for financial comparison.",
            )

    try:
        return compare_yearly_scenarios(
            latitude=latitude,
            longitude=longitude,
            scenarios=scenarios,
        )
    except Exception as e:
        logger.exception("Scenario comparison error")
        raise HTTPException(status_code=500, detail=str(e))
