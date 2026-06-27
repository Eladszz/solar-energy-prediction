from __future__ import annotations

from typing import Iterable

from app.defaults import (
    DEFAULT_CURRENCY,
    DEFAULT_ELECTRICITY_PRICE_PER_KWH,
    DEFAULT_MODEL_TYPE,
    DEFAULT_SYSTEM_CAPEX,
    DEFAULT_TRAINING_YEARS,
)
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


def calculate_series_mape(
    actual_values: Iterable[float], predicted_values: Iterable[float]
) -> float:
    errors = [
        calculate_mape(float(actual), float(predicted))
        for actual, predicted in zip(actual_values, predicted_values)
        if float(actual) != 0.0
    ]
    if not errors:
        return 0.0
    return sum(errors) / len(errors)


def calculate_mae(actual: float, predicted: float) -> float:
    return abs(actual - predicted)


def calculate_series_mae(
    actual_values: Iterable[float], predicted_values: Iterable[float]
) -> float:
    errors = [
        calculate_mae(float(actual), float(predicted))
        for actual, predicted in zip(actual_values, predicted_values)
    ]
    if not errors:
        return 0.0
    return sum(errors) / len(errors)


def calculate_bias_percent(
    actual_values: Iterable[float], predicted_values: Iterable[float]
) -> float:
    actual_total = sum(float(actual) for actual in actual_values)
    predicted_total = sum(float(predicted) for predicted in predicted_values)
    if actual_total == 0.0:
        return 0.0
    return ((predicted_total - actual_total) / actual_total) * 100


def calculate_mean_bias_kwh(
    actual_values: Iterable[float], predicted_values: Iterable[float]
) -> float:
    differences = [
        float(predicted) - float(actual)
        for actual, predicted in zip(actual_values, predicted_values)
    ]
    if not differences:
        return 0.0
    return sum(differences) / len(differences)


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
    model_type: str = DEFAULT_MODEL_TYPE,
    training_years: int = DEFAULT_TRAINING_YEARS,
    electricity_price_per_kwh: float = DEFAULT_ELECTRICITY_PRICE_PER_KWH,
    currency: str = DEFAULT_CURRENCY,
    system_capex: float = DEFAULT_SYSTEM_CAPEX,
) -> dict:
    system_loss_factor = compute_system_loss_factor(
        cleanliness=cleanliness,
        shading=shading,
    )

    actual_df = get_year_archive(
        latitude,
        longitude,
        year,
    )
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
        system_capex=system_capex,
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
        system_capex=system_capex,
    )

    yearly_mape = calculate_mape(
        actual_summary["yearly_kwh"],
        predicted_summary["yearly_kwh"],
    )
    yearly_mae = calculate_mae(
        actual_summary["yearly_kwh"],
        predicted_summary["yearly_kwh"],
    )
    monthly_mape = calculate_series_mape(
        actual_summary["monthly_kwh"],
        predicted_summary["monthly_kwh"],
    )
    monthly_mae = calculate_series_mae(
        actual_summary["monthly_kwh"],
        predicted_summary["monthly_kwh"],
    )
    bias_percent = calculate_bias_percent(
        [actual_summary["yearly_kwh"]],
        [predicted_summary["yearly_kwh"]],
    )
    bias_kwh = calculate_mean_bias_kwh(
        [actual_summary["yearly_kwh"]],
        [predicted_summary["yearly_kwh"]],
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
        "actual_annual_savings": actual_finance["annual_savings"],
        "predicted_annual_savings": predicted_finance["annual_savings"],
        "actual_simple_payback_years": actual_finance["simple_payback_years"],
        "predicted_simple_payback_years": predicted_finance["simple_payback_years"],
        "actual_monthly_kwh": actual_summary["monthly_kwh"],
        "predicted_monthly_kwh": predicted_summary["monthly_kwh"],
        "actual_monthly_estimated_value": actual_finance["monthly_estimated_value"],
        "predicted_monthly_estimated_value": predicted_finance[
            "monthly_estimated_value"
        ],
        "monthly_mae_kwh": round(monthly_mae, 1),
        "mape_percent": round(monthly_mape, 2),
        "yearly_mae_kwh": round(yearly_mae, 1),
        "yearly_mape_percent": round(yearly_mape, 2),
        "bias_percent": round(bias_percent, 2),
        "bias_kwh": round(bias_kwh, 1),
        "quality": quality,
        "financial_assumptions": predicted_finance["financial_assumptions"],
        "ml_metadata": predicted_weather_profile.ml_metadata,
    }
