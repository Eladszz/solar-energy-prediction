from __future__ import annotations

from dataclasses import dataclass, field
import logging

import numpy as np
import pandas as pd

from app.services.finance_service import build_financial_summary
from app.services.ml_forecast_service import (
    build_ml_metadata,
    build_hourly_time_index,
    predict_weather_profile,
    train_weather_regression_model,
)
from app.services.simulation_service import simulate_production_enhanced
from app.services.weather_archive_service import get_year_archive

logger = logging.getLogger(__name__)


SUPPORTED_MODEL_TYPES = {"physical", "ml"}


@dataclass
class WeatherProfileResult:
    df: pd.DataFrame
    forecast_year: int
    model_type_requested: str
    model_type_used: str
    weather_reference_year: int | None = None
    training_years: list[int] = field(default_factory=list)
    fallback_reason: str | None = None
    ml_metadata: dict | None = None


def normalize_model_type(model_type: str | None) -> str:
    normalized = (model_type or "physical").strip().lower()
    if normalized not in SUPPORTED_MODEL_TYPES:
        return "physical"
    return normalized


def resolve_forecast_year(requested_year: int | None) -> int:
    current_year = pd.Timestamp.now().year
    return requested_year or current_year


def get_last_complete_year() -> int:
    return pd.Timestamp.now().year - 1


def align_profile_to_year(df: pd.DataFrame, target_year: int) -> pd.DataFrame:
    target_times = build_hourly_time_index(target_year)
    aligned_df = df.copy().reset_index(drop=True)

    if len(aligned_df) == len(target_times):
        aligned_df["time"] = target_times
        return aligned_df

    source_times = pd.to_datetime(aligned_df["time"])
    aligned_df["month"] = source_times.dt.month
    aligned_df["day"] = source_times.dt.day
    aligned_df["hour"] = source_times.dt.hour

    target_df = pd.DataFrame({"time": target_times})
    target_df["month"] = target_df["time"].dt.month
    target_df["day"] = target_df["time"].dt.day
    target_df["hour"] = target_df["time"].dt.hour

    merged = target_df.merge(
        aligned_df[["month", "day", "hour", "irr", "temp"]],
        on=["month", "day", "hour"],
        how="left",
    )

    if merged["irr"].isna().any() or merged["temp"].isna().any():
        fallback_source = aligned_df.groupby(["month", "hour"])[["irr", "temp"]].mean()
        missing_mask = merged["irr"].isna() | merged["temp"].isna()
        if missing_mask.any():
            fallback_rows = (
                merged.loc[missing_mask, ["month", "hour"]]
                .merge(
                    fallback_source.reset_index(),
                    on=["month", "hour"],
                    how="left",
                )
                .reset_index(drop=True)
            )
            merged.loc[missing_mask, "irr"] = fallback_rows["irr"].to_numpy()
            merged.loc[missing_mask, "temp"] = fallback_rows["temp"].to_numpy()

    return merged[["time", "irr", "temp"]]


def compute_yearly_from_real_data(
    df,
    latitude,
    tilt,
    panel_area,
    efficiency,
    gamma,
    noct,
    system_loss_factor=0.87,
    ac_capacity_kw=15.0,
):
    working_df = df
    irr_list = working_df["irr"].fillna(0.0).tolist()
    temp_list = working_df["temp"].ffill().fillna(0.0).tolist()
    logger.info("Starting yearly production computation from weather profile...")
    hourly_kw = simulate_production_enhanced(
        irradiance_list=irr_list,
        temp_list=temp_list,
        latitude=latitude,
        tilt=tilt,
        panel_area=panel_area,
        efficiency=efficiency,
        gamma=gamma,
        noct=noct,
        system_loss_factor=system_loss_factor,
        ac_capacity_kw=ac_capacity_kw,
    )

    working_df["kw"] = hourly_kw
    working_df["kwh"] = working_df["kw"]
    working_df["month"] = pd.to_datetime(working_df["time"]).dt.month
    logger.info("Aggregating monthly and yearly production data...")
    monthly_series = (
        working_df.groupby("month")["kwh"].sum().reindex(range(1, 13), fill_value=0.0)
    )
    monthly = [round(float(value), 1) for value in monthly_series.tolist()]
    yearly = round(float(working_df["kwh"].sum()), 1)

    dc_capacity_kwp = panel_area * efficiency
    specific_yield = 0.0 if dc_capacity_kwp <= 0 else yearly / dc_capacity_kwp
    days_in_profile = max(pd.to_datetime(working_df["time"]).dt.normalize().nunique(), 1)
    avg_daily_kwh = yearly / days_in_profile

    logger.info(
        "Yearly production computed for %s hours with %.1f kWh yearly output",
        len(hourly_kw),
        yearly,
    )
    return {
        "monthly_kwh": monthly,
        "yearly_kwh": yearly,
        "specific_yield_kwh_per_kwp": round(specific_yield, 1),
        "avg_daily_kwh": round(avg_daily_kwh, 1),
    }


def prepare_physical_weather_profile(
    latitude: float,
    longitude: float,
    forecast_year: int,
    backtest_mode: bool = False,
) -> WeatherProfileResult:
    last_complete_year = get_last_complete_year()
    if backtest_mode:
        weather_reference_year = min(forecast_year - 1, last_complete_year)
    else:
        weather_reference_year = min(forecast_year, last_complete_year)

    weather_df = get_year_archive(latitude, longitude, weather_reference_year)
    aligned_df = align_profile_to_year(weather_df, forecast_year)
    fallback_reason = None
    if weather_reference_year != forecast_year:
        if backtest_mode:
            fallback_reason = (
                f"Archived weather for {forecast_year} is not used directly in the physical "
                f"backtest. The service reused {weather_reference_year} as the prior-year "
                "baseline profile."
            )
        else:
            fallback_reason = (
                f"Archived weather for {forecast_year} is not available yet. The physical "
                f"forecast reused archived weather from {weather_reference_year} as the "
                "baseline profile."
            )

    return WeatherProfileResult(
        df=aligned_df,
        forecast_year=forecast_year,
        model_type_requested="physical",
        model_type_used="physical",
        weather_reference_year=weather_reference_year,
        fallback_reason=fallback_reason,
    )


def prepare_ml_weather_profile(
    latitude: float,
    longitude: float,
    forecast_year: int,
    training_years: int,
) -> WeatherProfileResult:
    last_complete_year = get_last_complete_year()
    training_end_year = min(forecast_year - 1, last_complete_year)
    training_start_year = training_end_year - training_years + 1
    candidate_years = list(range(training_start_year, training_end_year + 1))

    history_frames: list[pd.DataFrame] = []
    years_used: list[int] = []
    for year in candidate_years:
        try:
            history_frames.append(get_year_archive(latitude, longitude, year))
            years_used.append(year)
        except Exception as exc:
            logger.warning("Skipping ML training year %s: %s", year, exc)

    if not history_frames:
        raise ValueError("No historical weather data was available for ML training")

    history_df = pd.concat(history_frames, ignore_index=True)
    model = train_weather_regression_model(history_df, years_used)
    predicted_weather_df = predict_weather_profile(model, forecast_year)

    return WeatherProfileResult(
        df=predicted_weather_df,
        forecast_year=forecast_year,
        model_type_requested="ml",
        model_type_used="ml",
        training_years=years_used,
        ml_metadata=build_ml_metadata(model),
    )


def build_forecast_weather_profile(
    latitude: float,
    longitude: float,
    forecast_year: int | None,
    model_type: str = "physical",
    training_years: int = 3,
    backtest_mode: bool = False,
) -> WeatherProfileResult:
    target_year = resolve_forecast_year(forecast_year)
    normalized_model_type = normalize_model_type(model_type)

    if normalized_model_type == "physical":
        return prepare_physical_weather_profile(
            latitude=latitude,
            longitude=longitude,
            forecast_year=target_year,
            backtest_mode=backtest_mode,
        )

    try:
        return prepare_ml_weather_profile(
            latitude=latitude,
            longitude=longitude,
            forecast_year=target_year,
            training_years=training_years,
        )
    except Exception as exc:
        logger.warning("ML forecast unavailable, falling back to physical baseline: %s", exc)
        fallback_profile = prepare_physical_weather_profile(
            latitude=latitude,
            longitude=longitude,
            forecast_year=target_year,
            backtest_mode=backtest_mode,
        )
        fallback_profile.model_type_requested = normalized_model_type
        fallback_profile.fallback_reason = (
            "ML forecast could not be generated. The service returned the physical "
            "baseline instead."
        )
        return fallback_profile


def build_yearly_forecast_response(
    weather_profile: WeatherProfileResult,
    latitude: float,
    longitude: float,
    tilt: float,
    panel_area: float,
    efficiency: float,
    gamma: float,
    noct: float,
    system_loss_factor: float,
    ac_capacity_kw: float,
    electricity_price_per_kwh: float,
    currency: str,
) -> dict:
    forecast = compute_yearly_from_real_data(
        df=weather_profile.df,
        latitude=latitude,
        tilt=tilt,
        panel_area=panel_area,
        efficiency=efficiency,
        gamma=gamma,
        noct=noct,
        system_loss_factor=system_loss_factor,
        ac_capacity_kw=ac_capacity_kw,
    )

    finance = build_financial_summary(
        monthly_kwh=forecast["monthly_kwh"],
        electricity_price_per_kwh=electricity_price_per_kwh,
        currency=currency,
    )

    response = {
        "location": (latitude, longitude),
        "forecast_year": weather_profile.forecast_year,
        "model_type_requested": weather_profile.model_type_requested,
        "model_type_used": weather_profile.model_type_used,
        "weather_reference_year": weather_profile.weather_reference_year,
        "training_years_used": weather_profile.training_years,
        "monthly_kwh": forecast["monthly_kwh"],
        "yearly_kwh": forecast["yearly_kwh"],
        "specific_yield_kwh_per_kwp": forecast["specific_yield_kwh_per_kwp"],
        "avg_daily_kwh": forecast["avg_daily_kwh"],
        "monthly_estimated_value": finance["monthly_estimated_value"],
        "yearly_estimated_value": finance["yearly_estimated_value"],
        "avg_monthly_estimated_value": finance["avg_monthly_estimated_value"],
        "financial_assumptions": finance["financial_assumptions"],
        "fallback_reason": weather_profile.fallback_reason,
        "ml_metadata": weather_profile.ml_metadata,
    }
    return response


def build_actual_year_summary(
    df: pd.DataFrame,
    latitude: float,
    tilt: float,
    panel_area: float,
    efficiency: float,
    gamma: float,
    noct: float,
    system_loss_factor: float,
    ac_capacity_kw: float,
    electricity_price_per_kwh: float,
    currency: str,
) -> dict:
    actual_summary = compute_yearly_from_real_data(
        df=df,
        latitude=latitude,
        tilt=tilt,
        panel_area=panel_area,
        efficiency=efficiency,
        gamma=gamma,
        noct=noct,
        system_loss_factor=system_loss_factor,
        ac_capacity_kw=ac_capacity_kw,
    )
    finance = build_financial_summary(
        monthly_kwh=actual_summary["monthly_kwh"],
        electricity_price_per_kwh=electricity_price_per_kwh,
        currency=currency,
    )
    actual_summary["monthly_estimated_value"] = finance["monthly_estimated_value"]
    actual_summary["yearly_estimated_value"] = finance["yearly_estimated_value"]
    actual_summary["avg_monthly_estimated_value"] = finance["avg_monthly_estimated_value"]
    actual_summary["financial_assumptions"] = finance["financial_assumptions"]
    return actual_summary
