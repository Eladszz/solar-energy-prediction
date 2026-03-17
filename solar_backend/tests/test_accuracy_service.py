from unittest.mock import patch

import pandas as pd
import pytest

from app.services.accuracy_service import calculate_mape, evaluate_yearly_accuracy
from app.services.yearly_forecast_service import WeatherProfileResult


def test_calculate_mape_basic():
    assert calculate_mape(100.0, 90.0) == 10.0
    assert calculate_mape(0.0, 50.0) == 0.0


@pytest.fixture
def actual_weather_df():
    times = pd.date_range("2025-01-01", periods=24, freq="h")
    return pd.DataFrame(
        {
            "time": times,
            "irr": [0.0] * 6 + [300.0] * 12 + [0.0] * 6,
            "temp": [20.0] * 24,
        }
    )


@pytest.fixture
def ml_profile():
    times = pd.date_range("2025-01-01", periods=24, freq="h")
    return WeatherProfileResult(
        df=pd.DataFrame(
            {
                "time": times,
                "irr": [0.0] * 6 + [280.0] * 12 + [0.0] * 6,
                "temp": [19.0] * 24,
            }
        ),
        forecast_year=2025,
        model_type_requested="ml",
        model_type_used="ml",
        training_years=[2022, 2023, 2024],
        ml_metadata={"training_metrics": {"irradiance": {"rmse": 42.0}}},
    )


@patch("app.services.accuracy_service.compute_yearly_from_real_data")
@patch("app.services.accuracy_service.build_forecast_weather_profile")
@patch("app.services.accuracy_service.compute_system_loss_factor")
@patch("app.services.accuracy_service.get_year_archive")
def test_evaluate_yearly_accuracy_returns_backtest_summary(
    mock_get_year_archive,
    mock_loss_factor,
    mock_build_profile,
    mock_compute_yearly,
    actual_weather_df,
    ml_profile,
):
    mock_get_year_archive.return_value = actual_weather_df
    mock_loss_factor.return_value = 0.86
    mock_build_profile.return_value = ml_profile
    mock_compute_yearly.side_effect = [
        {"yearly_kwh": 1200.0, "monthly_kwh": [100.0] * 12},
        {"yearly_kwh": 1080.0, "monthly_kwh": [90.0] * 12},
    ]

    result = evaluate_yearly_accuracy(
        latitude=32.08,
        longitude=34.78,
        year=2025,
        tilt=30.0,
        panel_area=80.0,
        efficiency=0.20,
        cleanliness="normal",
        shading="low",
        gamma=0.004,
        noct=45.0,
        ac_capacity_kw=15.0,
        model_type="ml",
        training_years=3,
        electricity_price_per_kwh=0.2,
        currency="USD",
        system_capex=2400.0,
    )

    assert result["year"] == 2025
    assert result["actual_yearly_kwh"] == 1200.0
    assert result["predicted_yearly_kwh"] == 1080.0
    assert result["mape_percent"] == 10.0
    assert result["yearly_mape_percent"] == 10.0
    assert result["quality"] == "GOOD"
    assert result["training_years_used"] == [2022, 2023, 2024]
    assert result["predicted_yearly_estimated_value"] == 216.0
    assert result["actual_yearly_estimated_value"] == 240.0
    assert result["predicted_annual_savings"] == 216.0
    assert result["actual_annual_savings"] == 240.0
    assert result["predicted_simple_payback_years"] == 11.1
    assert result["actual_simple_payback_years"] == 10.0
    assert result["ml_metadata"] == {"training_metrics": {"irradiance": {"rmse": 42.0}}}

    mock_build_profile.assert_called_once_with(
        latitude=32.08,
        longitude=34.78,
        forecast_year=2025,
        model_type="ml",
        training_years=3,
        backtest_mode=True,
        demo_mode=False,
        demo_scenario_id=None,
    )


@patch("app.services.accuracy_service.compute_yearly_from_real_data")
@patch("app.services.accuracy_service.build_forecast_weather_profile")
@patch("app.services.accuracy_service.compute_system_loss_factor")
@patch("app.services.accuracy_service.get_year_archive")
def test_evaluate_yearly_accuracy_zero_actual_energy_returns_zero_mape(
    mock_get_year_archive,
    mock_loss_factor,
    mock_build_profile,
    mock_compute_yearly,
    actual_weather_df,
    ml_profile,
):
    mock_get_year_archive.return_value = actual_weather_df
    mock_loss_factor.return_value = 0.85
    mock_build_profile.return_value = ml_profile
    mock_compute_yearly.side_effect = [
        {"yearly_kwh": 0.0, "monthly_kwh": [0.0] * 12},
        {"yearly_kwh": 150.0, "monthly_kwh": [12.5] * 12},
    ]

    result = evaluate_yearly_accuracy(
        latitude=32.08,
        longitude=34.78,
        year=2025,
        tilt=30.0,
        panel_area=80.0,
        efficiency=0.20,
        cleanliness="normal",
        shading="low",
        gamma=0.004,
        noct=45.0,
        ac_capacity_kw=15.0,
    )

    assert result["actual_yearly_kwh"] == 0.0
    assert result["mape_percent"] == 0.0
    assert result["yearly_mape_percent"] == 0.0


@patch("app.services.accuracy_service.compute_yearly_from_real_data")
@patch("app.services.accuracy_service.build_forecast_weather_profile")
@patch("app.services.accuracy_service.compute_system_loss_factor")
@patch("app.services.accuracy_service.get_year_archive")
def test_evaluate_yearly_accuracy_preserves_demo_metadata(
    mock_get_year_archive,
    mock_loss_factor,
    mock_build_profile,
    mock_compute_yearly,
    actual_weather_df,
):
    mock_get_year_archive.return_value = actual_weather_df
    mock_loss_factor.return_value = 0.86
    mock_build_profile.return_value = WeatherProfileResult(
        df=actual_weather_df,
        forecast_year=2025,
        model_type_requested="physical",
        model_type_used="physical",
        weather_reference_year=2024,
        data_source="demo",
        demo_scenario_id="phoenix_distribution_center",
        demo_scenario_name="Phoenix Distribution Center",
    )
    mock_compute_yearly.side_effect = [
        {"yearly_kwh": 1200.0, "monthly_kwh": [100.0] * 12},
        {"yearly_kwh": 1150.0, "monthly_kwh": [95.8] * 12},
    ]

    result = evaluate_yearly_accuracy(
        latitude=33.43,
        longitude=-112.01,
        year=2025,
        tilt=16.0,
        panel_area=180.0,
        efficiency=0.22,
        cleanliness="clean",
        shading="none",
        gamma=0.004,
        noct=46.0,
        ac_capacity_kw=38.0,
        demo_mode=True,
        demo_scenario_id="phoenix_distribution_center",
    )

    assert result["data_source"] == "demo"
    assert result["demo_scenario_id"] == "phoenix_distribution_center"
    assert result["demo_scenario_name"] == "Phoenix Distribution Center"
