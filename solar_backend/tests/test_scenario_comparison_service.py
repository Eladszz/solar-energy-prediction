from unittest.mock import patch

import pytest
import pandas as pd

from app.models.requests import BasePVRequest
from app.services.scenario_comparison_service import compare_yearly_scenarios
from app.services.yearly_forecast_service import WeatherProfileResult


@pytest.fixture
def sample_weather_profile():
    hours = pd.date_range("2026-01-01", periods=24, freq="h")
    return WeatherProfileResult(
        df=pd.DataFrame(
            {
                "time": hours,
                "irr": [0.0] * 6 + [200.0] * 12 + [0.0] * 6,
                "temp": [18.0] * 24,
            }
        ),
        forecast_year=2026,
        model_type_requested="physical",
        model_type_used="physical",
        weather_reference_year=2025,
    )


@pytest.fixture
def base_scenario():
    return BasePVRequest(
        latitude=32.08,
        longitude=34.78,
        year=2026,
        tilt=30.0,
        panel_area=80.0,
        panel_efficiency=0.20,
        cleanliness="normal",
        shading="low",
        ac_capacity_kw=15.0,
        gamma=0.004,
        noct=45.0,
        model_type="physical",
        electricity_price_per_kwh=0.18,
        currency="USD",
        training_years=3,
    )


@pytest.fixture
def larger_scenario():
    return BasePVRequest(
        latitude=32.08,
        longitude=34.78,
        year=2026,
        tilt=30.0,
        panel_area=100.0,
        panel_efficiency=0.20,
        cleanliness="clean",
        shading="none",
        ac_capacity_kw=18.0,
        gamma=0.004,
        noct=45.0,
        model_type="physical",
        electricity_price_per_kwh=0.18,
        currency="USD",
        training_years=3,
    )


def test_compare_yearly_scenarios_requires_at_least_one_scenario():
    with pytest.raises(ValueError, match="At least one scenario"):
        compare_yearly_scenarios(32.08, 34.78, [])


@patch("app.services.scenario_comparison_service.compute_yearly_from_real_data")
@patch("app.services.scenario_comparison_service.compute_system_loss_factor")
@patch("app.services.scenario_comparison_service.build_forecast_weather_profile")
def test_compare_yearly_scenarios_returns_energy_and_value_deltas(
    mock_build_profile,
    mock_loss_factor,
    mock_compute_yearly,
    sample_weather_profile,
    base_scenario,
    larger_scenario,
):
    mock_build_profile.return_value = sample_weather_profile
    mock_loss_factor.side_effect = [0.85, 0.92]
    mock_compute_yearly.side_effect = [
        {"yearly_kwh": 7200.0, "monthly_kwh": [600.0] * 12},
        {"yearly_kwh": 9000.0, "monthly_kwh": [750.0] * 12},
    ]

    result = compare_yearly_scenarios(
        latitude=32.08,
        longitude=34.78,
        scenarios=[base_scenario, larger_scenario],
    )

    assert result["year"] == 2026
    assert result["baseline_yearly_kwh"] == 7200.0
    assert result["baseline_yearly_estimated_value"] == 1296.0
    assert result["results"][0]["deviation_percent"] == 0.0
    assert result["results"][1]["deviation_percent"] == 25.0
    assert result["results"][1]["yearly_estimated_value"] == 1620.0
    assert result["results"][1]["value_deviation_percent"] == 25.0

    mock_build_profile.assert_called_once_with(
        latitude=32.08,
        longitude=34.78,
        forecast_year=2026,
        model_type="physical",
        training_years=3,
    )


@patch("app.services.scenario_comparison_service.compute_yearly_from_real_data")
@patch("app.services.scenario_comparison_service.compute_system_loss_factor")
@patch("app.services.scenario_comparison_service.build_forecast_weather_profile")
def test_compare_yearly_scenarios_uses_baseline_model_settings(
    mock_build_profile,
    mock_loss_factor,
    mock_compute_yearly,
    sample_weather_profile,
):
    baseline = BasePVRequest(
        latitude=32.08,
        longitude=34.78,
        year=2027,
        tilt=35.0,
        panel_area=90.0,
        panel_efficiency=0.21,
        cleanliness="normal",
        shading="low",
        ac_capacity_kw=17.0,
        gamma=0.004,
        noct=45.0,
        model_type="ml",
        electricity_price_per_kwh=0.22,
        currency="EUR",
        training_years=4,
    )
    mock_build_profile.return_value = sample_weather_profile
    mock_loss_factor.return_value = 0.87
    mock_compute_yearly.return_value = {
        "yearly_kwh": 8400.0,
        "monthly_kwh": [700.0] * 12,
    }

    result = compare_yearly_scenarios(
        latitude=32.08,
        longitude=34.78,
        scenarios=[baseline],
    )

    mock_build_profile.assert_called_once_with(
        latitude=32.08,
        longitude=34.78,
        forecast_year=2027,
        model_type="ml",
        training_years=4,
    )
    assert result["results"][0]["financial_assumptions"]["currency"] == "EUR"
