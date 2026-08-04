from __future__ import annotations

from dataclasses import dataclass
import logging
import math

import pandas as pd

from app.defaults import DEFAULT_AC_CAPACITY_KW
from app.exceptions.domain_exceptions import InvalidWeatherProfileError
from app.services.finance_service import build_financial_summary
from app.services.simulation_service import simulate_production_enhanced
from app.services.weather_archive_service import get_year_archive

logger = logging.getLogger(__name__)

PRODUCTION_MODEL = "simplified_physical_pv_model"
WEATHER_SOURCE = "Open-Meteo archive"


@dataclass
class WeatherProfileResult:
    df: pd.DataFrame
    requested_forecast_year: int
    weather_reference_year: int
    fallback_reason: str | None = None


def resolve_forecast_year(requested_year: int | None) -> int:
    return requested_year or pd.Timestamp.now().year


def get_last_complete_year() -> int:
    return pd.Timestamp.now().year - 1


def _hourly_time_index(year: int) -> pd.DatetimeIndex:
    return pd.date_range(f"{year}-01-01 00:00:00", f"{year}-12-31 23:00:00", freq="h")


def validate_hourly_weather_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Return a chronological hourly profile or reject malformed time/weather data."""
    required = {"time", "irr", "temp"}
    if not required.issubset(df.columns) or df.empty:
        raise InvalidWeatherProfileError(
            "Weather data is missing required hourly fields."
        )

    profile = df[["time", "irr", "temp"]].copy()
    try:
        profile["time"] = pd.to_datetime(profile["time"], errors="raise")
    except (TypeError, ValueError) as exc:
        raise InvalidWeatherProfileError("Weather timestamps are malformed.") from exc

    profile = profile.sort_values("time").reset_index(drop=True)
    if profile["time"].duplicated().any():
        raise InvalidWeatherProfileError("Weather timestamps must be unique.")
    if (
        len(profile) > 1
        and not profile["time"].diff().iloc[1:].eq(pd.Timedelta(hours=1)).all()
    ):
        raise InvalidWeatherProfileError(
            "Weather timestamps must use continuous one-hour intervals."
        )

    profile["irr"] = pd.to_numeric(profile["irr"], errors="coerce").fillna(0.0)
    profile["temp"] = pd.to_numeric(profile["temp"], errors="coerce").ffill().bfill()
    if profile["temp"].isna().any():
        raise InvalidWeatherProfileError(
            "Weather temperature data contains no usable values."
        )
    if (
        not profile[["irr", "temp"]]
        .map(lambda value: isinstance(value, (int, float)) and math.isfinite(value))
        .all()
        .all()
    ):
        raise InvalidWeatherProfileError(
            "Weather data contains invalid numeric values."
        )
    return profile


def align_profile_to_year(df: pd.DataFrame, target_year: int) -> pd.DataFrame:
    source = validate_hourly_weather_profile(df)
    target_times = _hourly_time_index(target_year)
    if len(source) == len(target_times):
        source["time"] = target_times
        return source

    source["month"] = source["time"].dt.month
    source["day"] = source["time"].dt.day
    source["hour"] = source["time"].dt.hour
    target = pd.DataFrame({"time": target_times})
    target["month"] = target["time"].dt.month
    target["day"] = target["time"].dt.day
    target["hour"] = target["time"].dt.hour
    merged = target.merge(
        source[["month", "day", "hour", "irr", "temp"]],
        on=["month", "day", "hour"],
        how="left",
    )
    fallback = source.groupby(["month", "hour"])[["irr", "temp"]].mean()
    missing = merged["irr"].isna() | merged["temp"].isna()
    if missing.any():
        values = merged.loc[missing, ["month", "hour"]].merge(
            fallback.reset_index(), on=["month", "hour"], how="left"
        )
        merged.loc[missing, "irr"] = values["irr"].to_numpy()
        merged.loc[missing, "temp"] = values["temp"].to_numpy()
    return validate_hourly_weather_profile(merged[["time", "irr", "temp"]])


def build_physical_weather_profile(
    latitude: float, longitude: float, forecast_year: int | None
) -> WeatherProfileResult:
    requested_year = resolve_forecast_year(forecast_year)
    reference_year = min(requested_year, get_last_complete_year())
    profile = align_profile_to_year(
        get_year_archive(latitude, longitude, reference_year), requested_year
    )
    fallback_reason = None
    if reference_year != requested_year:
        fallback_reason = (
            f"Archived weather for {requested_year} is not available yet. "
            f"The estimate reuses archived weather from {reference_year}."
        )
    return WeatherProfileResult(
        profile, requested_year, reference_year, fallback_reason
    )


def compute_yearly_from_hourly_weather(
    df: pd.DataFrame,
    latitude: float,
    tilt: float,
    panel_area: float,
    efficiency: float,
    gamma: float,
    noct: float,
    system_loss_factor: float,
    ac_capacity_kw: float = DEFAULT_AC_CAPACITY_KW,
) -> dict:
    """Convert hourly weather into monthly and annual energy in kWh."""
    profile = validate_hourly_weather_profile(df)
    hourly_kw = simulate_production_enhanced(
        profile["irr"].tolist(),
        profile["temp"].tolist(),
        latitude,
        tilt,
        panel_area,
        efficiency,
        gamma,
        noct,
        system_loss_factor,
        ac_capacity_kw,
    )
    profile["kwh"] = hourly_kw  # one-hour samples: average kW equals interval kWh
    profile["month"] = profile["time"].dt.month
    monthly_values = (
        profile.groupby("month")["kwh"].sum().reindex(range(1, 13), fill_value=0.0)
    )
    monthly = [round(float(value), 1) for value in monthly_values]
    yearly = round(float(sum(monthly)), 1)
    dc_capacity_kwp = panel_area * efficiency
    days = max(profile["time"].dt.normalize().nunique(), 1)
    return {
        "monthly_kwh": monthly,
        "yearly_kwh": yearly,
        "specific_yield_kwh_per_kwp": round(yearly / dc_capacity_kwp, 1),
        "avg_daily_kwh": round(yearly / days, 1),
    }


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
    system_capex: float,
) -> dict:
    forecast = compute_yearly_from_hourly_weather(
        weather_profile.df,
        latitude,
        tilt,
        panel_area,
        efficiency,
        gamma,
        noct,
        system_loss_factor,
        ac_capacity_kw,
    )
    finance = build_financial_summary(
        forecast["monthly_kwh"], electricity_price_per_kwh, currency, system_capex
    )
    return {
        "location": [latitude, longitude],
        "requested_forecast_year": weather_profile.requested_forecast_year,
        "production_model": PRODUCTION_MODEL,
        "weather_source": WEATHER_SOURCE,
        "weather_reference_year": weather_profile.weather_reference_year,
        **forecast,
        "monthly_estimated_value": finance["monthly_estimated_value"],
        "yearly_estimated_value": finance["yearly_estimated_value"],
        "annual_savings": finance["annual_savings"],
        "simple_payback_years": finance["simple_payback_years"],
        "avg_monthly_estimated_value": finance["avg_monthly_estimated_value"],
        "financial_assumptions": finance["financial_assumptions"],
        "fallback_reason": weather_profile.fallback_reason,
    }
