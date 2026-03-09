from __future__ import annotations

from typing import Iterable

from app.services.finance_service import build_financial_summary
from app.services.loss_service import compute_system_loss_factor
from app.services.weather_archive_service import get_year_archive
from app.services.yearly_forecast_service import (
    build_forecast_weather_profile,
    compute_yearly_from_real_data,
)


def calculate_mape(actual: float, predicted: float) -> float:
    if actual == 0:
        return 0.0
    return abs((actual - predicted) / actual) * 100


def calculate_series_mape(actual_values: Iterable[float], predicted_values: Iterable[float]) -> float:
    errors = [
        calculate_mape(float(actual), float(predicted))
        for actual, predicted in zip(actual_values, predicted_values)
        if float(actual) != 0.0
    ]
    if not errors:
        return 0.0
    return sum(errors) / len(errors)


def classify_quality(mape: float) -> str:
    if mape < 10:
        return "EXCELLENT"
    if mape < 25:
        return "GOOD"
    return "POOR"


def evaluate_yearly_accuracy(
    latitude: float,
    longitude: float,
    year: int,
    tilt: float,
    panel_area: float,
    efficiency: float,
    cleanliness: str,
    shading: str,
    gamma: float,
    noct: float,
    ac_capacity_kw: float,
    model_type: str = "physical",
    training_years: int = 3,
    electricity_price_per_kwh: float = 0.17,
    currency: str = "USD",
) -> dict:
    system_loss_factor = compute_system_loss_factor(
        cleanliness=cleanliness,
        shading=shading,
    )

    actual_df = get_year_archive(latitude, longitude, year)
    actual_summary = compute_yearly_from_real_data(
        df=actual_df.copy(),
        latitude=latitude,
        tilt=tilt,
        panel_area=panel_area,
        efficiency=efficiency,
        gamma=gamma,
        noct=noct,
        system_loss_factor=system_loss_factor,
        ac_capacity_kw=ac_capacity_kw,
    )
    actual_finance = build_financial_summary(
        monthly_kwh=actual_summary["monthly_kwh"],
        electricity_price_per_kwh=electricity_price_per_kwh,
        currency=currency,
    )

    predicted_weather_profile = build_forecast_weather_profile(
        latitude=latitude,
        longitude=longitude,
        forecast_year=year,
        model_type=model_type,
        training_years=training_years,
        backtest_mode=True,
    )
    predicted_summary = compute_yearly_from_real_data(
        df=predicted_weather_profile.df.copy(),
        latitude=latitude,
        tilt=tilt,
        panel_area=panel_area,
        efficiency=efficiency,
        gamma=gamma,
        noct=noct,
        system_loss_factor=system_loss_factor,
        ac_capacity_kw=ac_capacity_kw,
    )
    predicted_finance = build_financial_summary(
        monthly_kwh=predicted_summary["monthly_kwh"],
        electricity_price_per_kwh=electricity_price_per_kwh,
        currency=currency,
    )

    yearly_mape = calculate_mape(
        actual_summary["yearly_kwh"],
        predicted_summary["yearly_kwh"],
    )
    monthly_mape = calculate_series_mape(
        actual_summary["monthly_kwh"],
        predicted_summary["monthly_kwh"],
    )
    quality = classify_quality(monthly_mape)

    return {
        "year": year,
        "model_type_requested": model_type,
        "model_type_used": predicted_weather_profile.model_type_used,
        "weather_reference_year": predicted_weather_profile.weather_reference_year,
        "training_years_used": predicted_weather_profile.training_years,
        "fallback_reason": predicted_weather_profile.fallback_reason,
        "actual_yearly_kwh": round(actual_summary["yearly_kwh"], 1),
        "predicted_yearly_kwh": round(predicted_summary["yearly_kwh"], 1),
        "actual_yearly_estimated_value": actual_finance["yearly_estimated_value"],
        "predicted_yearly_estimated_value": predicted_finance["yearly_estimated_value"],
        "actual_monthly_kwh": actual_summary["monthly_kwh"],
        "predicted_monthly_kwh": predicted_summary["monthly_kwh"],
        "actual_monthly_estimated_value": actual_finance["monthly_estimated_value"],
        "predicted_monthly_estimated_value": predicted_finance["monthly_estimated_value"],
        "mape_percent": round(monthly_mape, 2),
        "yearly_mape_percent": round(yearly_mape, 2),
        "quality": quality,
        "financial_assumptions": predicted_finance["financial_assumptions"],
        "ml_metadata": predicted_weather_profile.ml_metadata,
    }
