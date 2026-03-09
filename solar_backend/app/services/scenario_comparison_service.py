from __future__ import annotations

from typing import Dict, List

from app.models.requests import BasePVRequest
from app.services.finance_service import build_financial_summary
from app.services.loss_service import compute_system_loss_factor
from app.services.yearly_forecast_service import (
    build_forecast_weather_profile,
    compute_yearly_from_real_data,
)


def compare_yearly_scenarios(
    latitude: float,
    longitude: float,
    scenarios: List[BasePVRequest],
) -> Dict:
    if not scenarios:
        raise ValueError("At least one scenario is required")

    baseline_request = scenarios[0]
    weather_profile = build_forecast_weather_profile(
        latitude=latitude,
        longitude=longitude,
        forecast_year=baseline_request.year,
        model_type=baseline_request.model_type,
        training_years=baseline_request.training_years,
    )

    results = []

    for scenario in scenarios:
        system_loss_factor = compute_system_loss_factor(
            cleanliness=scenario.cleanliness,
            shading=scenario.shading,
        )

        forecast = compute_yearly_from_real_data(
            df=weather_profile.df.copy(),
            latitude=latitude,
            tilt=scenario.tilt,
            panel_area=scenario.panel_area,
            efficiency=scenario.panel_efficiency,
            gamma=scenario.gamma,
            noct=scenario.noct,
            system_loss_factor=system_loss_factor,
            ac_capacity_kw=scenario.ac_capacity_kw,
        )
        finance = build_financial_summary(
            monthly_kwh=forecast["monthly_kwh"],
            electricity_price_per_kwh=scenario.electricity_price_per_kwh,
            currency=scenario.currency,
        )

        results.append(
            {
                "scenario": scenario,
                "yearly_kwh": forecast["yearly_kwh"],
                "monthly_kwh": forecast["monthly_kwh"],
                "yearly_estimated_value": finance["yearly_estimated_value"],
                "monthly_estimated_value": finance["monthly_estimated_value"],
                "financial_assumptions": finance["financial_assumptions"],
            }
        )

    baseline = results[0]["yearly_kwh"]
    baseline_value = results[0]["yearly_estimated_value"]

    for result in results:
        if baseline == 0:
            result["deviation_percent"] = 0.0
        else:
            result["deviation_percent"] = round(
                100 * (result["yearly_kwh"] - baseline) / baseline,
                2,
            )

        if baseline_value == 0:
            result["value_deviation_percent"] = 0.0
        else:
            result["value_deviation_percent"] = round(
                100 * (result["yearly_estimated_value"] - baseline_value)
                / baseline_value,
                2,
            )

    return {
        "year": weather_profile.forecast_year,
        "model_type_requested": weather_profile.model_type_requested,
        "model_type_used": weather_profile.model_type_used,
        "weather_reference_year": weather_profile.weather_reference_year,
        "training_years_used": weather_profile.training_years,
        "fallback_reason": weather_profile.fallback_reason,
        "baseline_yearly_kwh": baseline,
        "baseline_yearly_estimated_value": baseline_value,
        "results": results,
    }
