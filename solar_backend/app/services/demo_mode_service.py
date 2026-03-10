from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import config


DEMO_FORECAST_START = pd.Timestamp("2026-06-21 00:00:00")
DEMO_CATALOG_PATH = Path(__file__).resolve().parents[3] / "demo" / "catalog.json"


@dataclass(frozen=True)
class DemoScenario:
    id: str
    name: str
    address: str
    country: str
    city: str
    street: str
    number: str
    latitude: float
    longitude: float
    timezone: str
    description: str
    system_defaults: dict[str, Any]
    comparison_variants: list[dict[str, Any]]
    weather_profile: dict[str, float]


def is_demo_mode_enabled(requested_demo_mode: bool | None = None) -> bool:
    if requested_demo_mode is None:
        return bool(config.DEMO_MODE)
    return bool(requested_demo_mode or config.DEMO_MODE)


@lru_cache()
def load_demo_catalog() -> dict[str, DemoScenario]:
    raw_payload = json.loads(DEMO_CATALOG_PATH.read_text())
    scenarios = {}
    for raw_scenario in raw_payload["scenarios"]:
        scenario = DemoScenario(**raw_scenario)
        scenarios[scenario.id] = scenario
    return scenarios


@lru_cache()
def get_default_demo_scenario_id() -> str:
    raw_payload = json.loads(DEMO_CATALOG_PATH.read_text())
    return str(raw_payload["default_scenario_id"])


def resolve_demo_scenario(
    latitude: float | None = None,
    longitude: float | None = None,
    demo_scenario_id: str | None = None,
) -> DemoScenario:
    scenarios = load_demo_catalog()
    scenario_id = demo_scenario_id or config.DEMO_DEFAULT_SCENARIO_ID or get_default_demo_scenario_id()
    if scenario_id in scenarios:
        return scenarios[scenario_id]

    if latitude is None or longitude is None:
        return scenarios[get_default_demo_scenario_id()]

    return min(
        scenarios.values(),
        key=lambda scenario: (
            (scenario.latitude - latitude) ** 2 + (scenario.longitude - longitude) ** 2
        ),
    )


def build_demo_response_metadata(scenario: DemoScenario) -> dict[str, str]:
    return {
        "data_source": "demo",
        "demo_scenario_id": scenario.id,
        "demo_scenario_name": scenario.name,
    }


def _build_irradiance(timestamp: pd.Timestamp, profile: dict[str, float]) -> float:
    day_of_year = float(timestamp.dayofyear)
    hour = timestamp.hour + (timestamp.minute / 60.0)
    daylight_hours = 12.0 + 4.0 * math.sin(2.0 * math.pi * (day_of_year - 80.0) / 365.25)
    sunrise_shift = profile.get("sunrise_shift_hours", 0.0)
    sunrise_hour = 12.0 - (daylight_hours / 2.0) + sunrise_shift
    sunset_hour = 12.0 + (daylight_hours / 2.0) + sunrise_shift
    if hour <= sunrise_hour or hour >= sunset_hour:
        return 0.0

    daylight_progress = (hour - sunrise_hour) / max(sunset_hour - sunrise_hour, 1e-6)
    solar_arc = math.sin(math.pi * daylight_progress)
    solar_shape = solar_arc**1.55
    seasonal_factor = 1.0 + profile.get("seasonality", 0.2) * math.sin(
        2.0 * math.pi * (day_of_year - 172.0) / 365.25
    )
    cloudiness = profile.get("cloudiness", 0.1)
    cloud_factor = 1.0 - cloudiness * (
        0.55 + 0.45 * math.sin(2.0 * math.pi * (day_of_year + hour) / 17.0)
    )
    cloud_factor = min(max(cloud_factor, 0.55), 1.0)
    year_factor = 1.0 + profile.get("year_solar_trend", 0.01) * (timestamp.year - 2025)
    return round(
        max(
            0.0,
            920.0
            * profile.get("solar_scale", 1.0)
            * seasonal_factor
            * solar_shape
            * cloud_factor
            * year_factor,
        ),
        3,
    )


def _build_temperature(timestamp: pd.Timestamp, profile: dict[str, float]) -> float:
    day_of_year = float(timestamp.dayofyear)
    hour = timestamp.hour + (timestamp.minute / 60.0)
    base = profile.get("temperature_base_c", 20.0)
    seasonal = profile.get("temperature_seasonality", 8.0) * math.sin(
        2.0 * math.pi * (day_of_year - 172.0) / 365.25
    )
    daily = profile.get("daily_temp_swing", 5.0) * math.sin(
        2.0 * math.pi * (hour - 14.0) / 24.0
    )
    year_offset = profile.get("year_temperature_trend", 0.15) * (timestamp.year - 2025)
    return round(base + seasonal + daily + year_offset, 3)


def _build_hourly_payload(
    scenario: DemoScenario,
    timestamps: pd.DatetimeIndex,
) -> dict[str, Any]:
    irradiance = [_build_irradiance(timestamp, scenario.weather_profile) for timestamp in timestamps]
    temperature = [_build_temperature(timestamp, scenario.weather_profile) for timestamp in timestamps]
    return {
        "latitude": scenario.latitude,
        "longitude": scenario.longitude,
        "timezone": scenario.timezone,
        "hourly": {
            "time": [timestamp.strftime("%Y-%m-%dT%H:%M") for timestamp in timestamps],
            "shortwave_radiation": irradiance,
            "temperature_2m": temperature,
        },
        **build_demo_response_metadata(scenario),
    }


def build_demo_forecast(
    *,
    latitude: float,
    longitude: float,
    days: int = 1,
    demo_scenario_id: str | None = None,
) -> dict[str, Any]:
    scenario = resolve_demo_scenario(
        latitude=latitude,
        longitude=longitude,
        demo_scenario_id=demo_scenario_id,
    )
    total_hours = max(int(days), 1) * 24
    timestamps = pd.date_range(DEMO_FORECAST_START, periods=total_hours, freq="h")
    return _build_hourly_payload(scenario, timestamps)


def build_demo_archive(
    *,
    latitude: float,
    longitude: float,
    year: int,
    demo_scenario_id: str | None = None,
) -> pd.DataFrame:
    scenario = resolve_demo_scenario(
        latitude=latitude,
        longitude=longitude,
        demo_scenario_id=demo_scenario_id,
    )
    timestamps = pd.date_range(
        start=f"{year}-01-01 00:00:00",
        end=f"{year}-12-31 23:00:00",
        freq="h",
    )
    hourly_payload = _build_hourly_payload(scenario, timestamps)
    return pd.DataFrame(
        {
            "time": pd.to_datetime(hourly_payload["hourly"]["time"]),
            "irr": hourly_payload["hourly"]["shortwave_radiation"],
            "temp": hourly_payload["hourly"]["temperature_2m"],
        }
    )
