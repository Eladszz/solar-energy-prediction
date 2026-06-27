from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from app.services.benchmark_service import evaluate_forecast_benchmark
from app.services.yearly_forecast_service import WeatherProfileResult


def build_profile(
    *,
    year: int,
    requested: str,
    used: str,
    weather_reference_year: int | None = None,
    training_years: list[int] | None = None,
    fallback_reason: str | None = None,
) -> WeatherProfileResult:
    df = pd.DataFrame(
        {
            "time": pd.date_range(f"{year}-01-01", periods=24, freq="h"),
            "irr": [0.0] * 24,
            "temp": [20.0] * 24,
        }
    )
    return WeatherProfileResult(
        df=df,
        forecast_year=year,
        model_type_requested=requested,
        model_type_used=used,
        weather_reference_year=weather_reference_year,
        training_years=training_years or [],
        fallback_reason=fallback_reason,
    )


@patch("app.services.benchmark_service.compute_yearly_from_real_data")
@patch("app.services.benchmark_service._build_predicted_profile")
@patch("app.services.benchmark_service._build_actual_summary")
@patch("app.services.benchmark_service.compute_system_loss_factor", return_value=0.86)
def test_evaluate_forecast_benchmark_returns_comparison_metrics(
    _mock_loss_factor,
    mock_actual_summary,
    mock_build_profile,
    mock_compute_yearly,
):
    mock_actual_summary.side_effect = [
        {"yearly_kwh": 1200.0, "monthly_kwh": [100.0] * 12},
        {"yearly_kwh": 1320.0, "monthly_kwh": [110.0] * 12},
    ]
    mock_build_profile.side_effect = [
        build_profile(year=2024, requested="physical", used="physical", weather_reference_year=2023),
        build_profile(year=2025, requested="physical", used="physical", weather_reference_year=2024),
        build_profile(
            year=2024,
            requested="ml",
            used="physical",
            weather_reference_year=2023,
            training_years=[2021, 2022, 2023],
            fallback_reason="ML baseline unavailable for this year.",
        ),
        build_profile(
            year=2025,
            requested="ml",
            used="ml",
            training_years=[2022, 2023, 2024],
        ),
        build_profile(
            year=2024,
            requested="naive",
            used="naive",
            training_years=[2021, 2022, 2023],
        ),
        build_profile(
            year=2025,
            requested="naive",
            used="naive",
            training_years=[2022, 2023, 2024],
        ),
    ]
    mock_compute_yearly.side_effect = [
        {"yearly_kwh": 1140.0, "monthly_kwh": [95.0] * 12},
        {"yearly_kwh": 1260.0, "monthly_kwh": [105.0] * 12},
        {"yearly_kwh": 1224.0, "monthly_kwh": [102.0] * 12},
        {"yearly_kwh": 1296.0, "monthly_kwh": [108.0] * 12},
        {"yearly_kwh": 1080.0, "monthly_kwh": [90.0] * 12},
        {"yearly_kwh": 1200.0, "monthly_kwh": [100.0] * 12},
    ]

    result = evaluate_forecast_benchmark(
        latitude=32.08,
        longitude=34.78,
        year=2025,
        benchmark_years=2,
        tilt=30.0,
        panel_area=80.0,
        efficiency=0.20,
        cleanliness="normal",
        shading="low",
        gamma=0.004,
        noct=45.0,
        ac_capacity_kw=15.0,
        training_years=3,
    )

    assert result["evaluation_years"] == [2024, 2025]
    assert result["benchmark_years_requested"] == 2
    assert result["training_window_years"] == 3
    assert result["approaches"][0]["approach"] == "physical"
    assert result["approaches"][0]["metrics"]["monthly_mape_percent"] == 4.77
    assert result["approaches"][0]["metrics"]["yearly_mae_kwh"] == 60.0
    assert result["approaches"][0]["metrics"]["bias_percent"] == -4.76
    assert result["approaches"][1]["approach"] == "ml"
    assert result["approaches"][1]["metrics"]["monthly_mape_percent"] == 1.91
    assert result["approaches"][1]["metrics"]["bias_percent"] == 0.0
    assert result["approaches"][1]["fallback_years"] == [2024]
    assert result["approaches"][1]["yearly_results"][0]["model_type_used"] == "physical"
    assert result["approaches"][2]["approach"] == "naive"
    assert result["approaches"][2]["metrics"]["monthly_mape_percent"] == 9.55
    assert result["approaches"][2]["metrics"]["bias_kwh"] == -120.0
