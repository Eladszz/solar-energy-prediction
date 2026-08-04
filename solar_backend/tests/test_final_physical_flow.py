from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.exceptions.domain_exceptions import InvalidWeatherProfileError
from app.main import app
from app.models.requests import ScenarioComparisonRequest
from app.services.scenario_comparison_service import compare_yearly_scenarios
from app.services.simulation_service import simulate_production_enhanced
from app.services.yearly_forecast_service import (
    WeatherProfileResult,
    compute_yearly_from_hourly_weather,
    validate_hourly_weather_profile,
)


def hourly_profile(hours: int = 24) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": pd.date_range("2025-01-01", periods=hours, freq="h"),
            "irr": [0.0] * 6 + [600.0] * 12 + [0.0] * (hours - 18),
            "temp": [20.0] * hours,
        }
    )


def simulation(
    area: float = 80.0, loss: float = 0.9, clip: float = 100.0
) -> list[float]:
    return simulate_production_enhanced(
        [0.0, -1.0, 800.0],
        [20.0] * 3,
        32.0,
        30.0,
        area,
        0.2,
        0.004,
        45.0,
        loss,
        clip,
    )


def test_physical_power_invariants_and_scaling():
    base = simulation(area=40.0)
    larger = simulation(area=80.0)
    assert base[0:2] == [0.0, 0.0]
    assert all(value >= 0.0 for value in base)
    assert larger[2] > base[2]
    assert simulation(loss=0.7)[2] < simulation(loss=0.9)[2]
    assert simulation(clip=2.0)[2] == 2.0


def test_monthly_energy_sums_to_yearly_energy():
    result = compute_yearly_from_hourly_weather(
        hourly_profile(), 32.0, 30.0, 80.0, 0.2, 0.004, 45.0, 0.9, 100.0
    )
    assert sum(result["monthly_kwh"]) == pytest.approx(result["yearly_kwh"], abs=0.1)


@pytest.mark.parametrize(
    "times",
    [
        ["2025-01-01 00:00", "2025-01-01 00:00"],
        ["2025-01-01 00:00", "2025-01-01 02:00"],
    ],
)
def test_duplicate_and_irregular_timestamps_are_rejected(times):
    frame = pd.DataFrame({"time": times, "irr": [0.0, 10.0], "temp": [20.0, 20.0]})
    with pytest.raises(InvalidWeatherProfileError):
        validate_hourly_weather_profile(frame)


def test_null_weather_values_are_controlled():
    frame = pd.DataFrame(
        {
            "time": pd.date_range("2025-01-01", periods=2, freq="h"),
            "irr": [None, 10],
            "temp": [None, None],
        }
    )
    with pytest.raises(InvalidWeatherProfileError, match="temperature"):
        validate_hourly_weather_profile(frame)


def scenario_payload(names=("Base", "Option")) -> dict:
    scenario = {
        "tilt": 30,
        "panel_area": 80,
        "panel_efficiency": 0.2,
        "cleanliness": "normal",
        "shading": "low",
        "ac_capacity_kw": 15,
        "gamma": 0.004,
        "noct": 45,
        "system_capex": 60000,
    }
    return {
        "context": {"latitude": 32.0, "longitude": 34.0, "year": 2025},
        "scenarios": [{"name": name, **scenario} for name in names],
    }


def test_duplicate_scenario_names_are_rejected():
    with pytest.raises(ValidationError, match="unique"):
        ScenarioComparisonRequest(**scenario_payload(("Same", " same ")))


@patch("app.services.scenario_comparison_service.build_physical_weather_profile")
def test_scenarios_build_one_profile_and_apply_independent_parameters(build_profile):
    build_profile.return_value = WeatherProfileResult(hourly_profile(), 2025, 2025)
    request = ScenarioComparisonRequest(**scenario_payload())
    request.scenarios[1].panel_area = 100
    result = compare_yearly_scenarios(request.context, request.scenarios)
    build_profile.assert_called_once()
    assert result["results"][1]["yearly_kwh"] > result["results"][0]["yearly_kwh"]


@patch("app.services.weather_archive_service.requests.get")
def test_yearly_route_completes_with_only_open_meteo_transport_mocked(request_get):
    times = pd.date_range("2025-01-01", "2025-12-31 23:00", freq="h")
    request_get.return_value.status_code = 200
    request_get.return_value.json.return_value = {
        "hourly": {
            "time": times.strftime("%Y-%m-%dT%H:%M").tolist(),
            "shortwave_radiation": [
                0.0 if t.hour < 6 or t.hour > 18 else 500.0 for t in times
            ],
            "temperature_2m": [20.0] * len(times),
        }
    }
    response = TestClient(app).post(
        "/forecast/yearly",
        json={"latitude": 32.0, "longitude": 34.0, "year": 2025},
    )
    assert response.status_code == 200
    assert response.json()["production_model"] == "simplified_physical_pv_model"
    assert len(response.json()["monthly_kwh"]) == 12


def test_removed_evaluation_routes_are_not_registered():
    paths = {route.path for route in app.routes}
    assert "/evaluation/accuracy" not in paths
    assert "/evaluation/benchmark" not in paths


@patch("app.routers.simulate_router.get_weather_forecast")
def test_daily_invalid_weather_returns_controlled_error(get_weather):
    get_weather.return_value = {
        "hourly": {
            "time": ["2025-01-01T00:00"],
            "shortwave_radiation": [None],
            "temperature_2m": [None],
        }
    }
    response = TestClient(app).post(
        "/simulate", json={"latitude": 32.0, "longitude": 34.0}
    )
    assert response.status_code == 502
    assert "temperature" in response.json()["detail"]
