from __future__ import annotations

from typing import Dict

from app.exceptions.domain_exceptions import EmptyScenarioComparisonError
from app.models.requests import ScenarioComparisonContext, ScenarioComparisonScenario
from app.services.finance_service import build_financial_summary
from app.services.loss_service import compute_system_loss_factor
from app.services.yearly_forecast_service import (
    build_forecast_weather_profile,
    compute_yearly_from_real_data,
)


def compare_yearly_scenarios(
    context: ScenarioComparisonContext,
    scenarios: list[ScenarioComparisonScenario],
) -> Dict:
    if not scenarios:
        raise EmptyScenarioComparisonError()

    weather_profile = build_forecast_weather_profile(
        latitude=context.latitude,
        longitude=context.longitude,
        forecast_year=context.year,
        model_type=context.model_type,
        training_years=context.training_years,
    )

    results = []

    for scenario in scenarios:
        system_loss_factor = compute_system_loss_factor(
            cleanliness=scenario.cleanliness,
            shading=scenario.shading,
        )

        forecast = compute_yearly_from_real_data(
            df=weather_profile.df.copy(),
            latitude=context.latitude,
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
            electricity_price_per_kwh=context.electricity_price_per_kwh,
            currency=context.currency,
            system_capex=scenario.system_capex,
        )

        results.append(
            {
                "scenario": scenario.model_dump(),
                "yearly_kwh": forecast["yearly_kwh"],
                "monthly_kwh": forecast["monthly_kwh"],
                "yearly_estimated_value": finance["yearly_estimated_value"],
                "annual_savings": finance["annual_savings"],
                "simple_payback_years": finance["simple_payback_years"],
                "monthly_estimated_value": finance["monthly_estimated_value"],
                "financial_assumptions": finance["financial_assumptions"],
            }
        )

    baseline = results[0]["yearly_kwh"]
    baseline_value = results[0]["yearly_estimated_value"]
    baseline_annual_savings = results[0]["annual_savings"]
    baseline_simple_payback = results[0]["simple_payback_years"]

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
                100
                * (result["yearly_estimated_value"] - baseline_value)
                / baseline_value,
                2,
            )

        if baseline_simple_payback is None or result["simple_payback_years"] is None:
            result["payback_delta_years"] = None
        else:
            result["payback_delta_years"] = round(
                result["simple_payback_years"] - baseline_simple_payback,
                1,
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
        "baseline_annual_savings": baseline_annual_savings,
        "baseline_simple_payback_years": baseline_simple_payback,
        "results": results,
    }
