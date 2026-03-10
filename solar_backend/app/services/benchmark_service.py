from __future__ import annotations

from collections.abc import Callable

from app.services.accuracy_service import (
    calculate_bias_percent,
    calculate_mae,
    calculate_mape,
    calculate_mean_bias_kwh,
    calculate_series_mae,
    calculate_series_mape,
)
from app.services.loss_service import compute_system_loss_factor
from app.services.weather_archive_service import get_year_archive
from app.services.yearly_forecast_service import (
    WeatherProfileResult,
    build_forecast_weather_profile,
    build_weather_profile_metadata,
    compute_yearly_from_real_data,
    get_last_complete_year,
    prepare_naive_weather_profile,
)


BENCHMARK_REFERENCE_NOTE = (
    "The benchmark reference is a production proxy built by replaying archived actual weather "
    "through the shared PV simulation stack. This compares forecasting approaches consistently, "
    "but it is not a plant telemetry calibration study."
)


APPROACH_DESCRIPTIONS = {
    "physical": (
        "Deterministic rule-based baseline that reuses archived prior-year weather for the "
        "evaluation year."
    ),
    "ml": (
        "Lightweight regression baseline trained on historical hourly weather before converting "
        "the predicted profile through the same PV simulation stack."
    ),
    "naive": (
        "Simple climatology baseline that averages recent historical hourly weather patterns by "
        "calendar position."
    ),
}

APPROACH_LABELS = {
    "physical": "Physical",
    "ml": "ML",
    "naive": "Naive",
}


def _resolve_evaluation_years(requested_year: int | None, benchmark_years: int) -> list[int]:
    last_complete_year = get_last_complete_year()
    evaluation_end_year = min(requested_year or last_complete_year, last_complete_year)
    evaluation_start_year = max(2000, evaluation_end_year - benchmark_years + 1)
    return list(range(evaluation_start_year, evaluation_end_year + 1))


def _build_actual_summary(
    *,
    latitude: float,
    longitude: float,
    year: int,
    tilt: float,
    panel_area: float,
    efficiency: float,
    gamma: float,
    noct: float,
    system_loss_factor: float,
    ac_capacity_kw: float,
    demo_mode: bool,
    demo_scenario_id: str | None,
) -> dict:
    actual_df = get_year_archive(
        latitude,
        longitude,
        year,
        demo_mode=demo_mode,
        demo_scenario_id=demo_scenario_id,
    )
    return compute_yearly_from_real_data(
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


def _build_predicted_profile(
    *,
    approach: str,
    latitude: float,
    longitude: float,
    year: int,
    training_years: int,
    demo_mode: bool,
    demo_scenario_id: str | None,
) -> WeatherProfileResult:
    if approach == "naive":
        return prepare_naive_weather_profile(
            latitude=latitude,
            longitude=longitude,
            forecast_year=year,
            training_years=training_years,
            demo_mode=demo_mode,
            demo_scenario_id=demo_scenario_id,
        )

    return build_forecast_weather_profile(
        latitude=latitude,
        longitude=longitude,
        forecast_year=year,
        model_type=approach,
        training_years=training_years,
        backtest_mode=True,
        demo_mode=demo_mode,
        demo_scenario_id=demo_scenario_id,
    )


def _aggregate_metrics(yearly_results: list[dict]) -> dict:
    actual_monthly_values = [
        month_value
        for result in yearly_results
        for month_value in result["actual_monthly_kwh"]
    ]
    predicted_monthly_values = [
        month_value
        for result in yearly_results
        for month_value in result["predicted_monthly_kwh"]
    ]
    actual_yearly_values = [result["actual_yearly_kwh"] for result in yearly_results]
    predicted_yearly_values = [result["predicted_yearly_kwh"] for result in yearly_results]

    return {
        "monthly_mape_percent": round(
            calculate_series_mape(actual_monthly_values, predicted_monthly_values),
            2,
        ),
        "monthly_mae_kwh": round(
            calculate_series_mae(actual_monthly_values, predicted_monthly_values),
            1,
        ),
        "yearly_mape_percent": round(
            calculate_series_mape(actual_yearly_values, predicted_yearly_values),
            2,
        ),
        "yearly_mae_kwh": round(
            calculate_series_mae(actual_yearly_values, predicted_yearly_values),
            1,
        ),
        "bias_percent": round(
            calculate_bias_percent(actual_yearly_values, predicted_yearly_values),
            2,
        ),
        "bias_kwh": round(
            calculate_mean_bias_kwh(actual_yearly_values, predicted_yearly_values),
            1,
        ),
    }


def _evaluate_approach(
    *,
    approach: str,
    evaluation_years: list[int],
    latitude: float,
    longitude: float,
    tilt: float,
    panel_area: float,
    efficiency: float,
    gamma: float,
    noct: float,
    system_loss_factor: float,
    ac_capacity_kw: float,
    training_years: int,
    demo_mode: bool,
    demo_scenario_id: str | None,
    actual_summary_builder: Callable[[int], dict],
) -> dict:
    yearly_results: list[dict] = []
    fallback_years: list[int] = []

    for year in evaluation_years:
        actual_summary = actual_summary_builder(year)
        predicted_profile = _build_predicted_profile(
            approach=approach,
            latitude=latitude,
            longitude=longitude,
            year=year,
            training_years=training_years,
            demo_mode=demo_mode,
            demo_scenario_id=demo_scenario_id,
        )
        predicted_summary = compute_yearly_from_real_data(
            df=predicted_profile.df.copy(),
            latitude=latitude,
            tilt=tilt,
            panel_area=panel_area,
            efficiency=efficiency,
            gamma=gamma,
            noct=noct,
            system_loss_factor=system_loss_factor,
            ac_capacity_kw=ac_capacity_kw,
        )

        if predicted_profile.fallback_reason:
            fallback_years.append(year)

        actual_yearly_kwh = float(actual_summary["yearly_kwh"])
        predicted_yearly_kwh = float(predicted_summary["yearly_kwh"])
        yearly_results.append(
            {
                "year": year,
                "actual_yearly_kwh": round(actual_yearly_kwh, 1),
                "predicted_yearly_kwh": round(predicted_yearly_kwh, 1),
                "actual_monthly_kwh": actual_summary["monthly_kwh"],
                "predicted_monthly_kwh": predicted_summary["monthly_kwh"],
                "yearly_mape_percent": round(
                    calculate_mape(actual_yearly_kwh, predicted_yearly_kwh),
                    2,
                ),
                "yearly_mae_kwh": round(
                    calculate_mae(actual_yearly_kwh, predicted_yearly_kwh),
                    1,
                ),
                "yearly_bias_kwh": round(predicted_yearly_kwh - actual_yearly_kwh, 1),
                "model_type_used": predicted_profile.model_type_used,
                "weather_reference_year": predicted_profile.weather_reference_year,
                "training_years_used": predicted_profile.training_years,
                "fallback_reason": predicted_profile.fallback_reason,
            }
        )

    return {
        "approach": approach,
        "label": APPROACH_LABELS[approach],
        "description": APPROACH_DESCRIPTIONS[approach],
        "metrics": _aggregate_metrics(yearly_results),
        "yearly_results": yearly_results,
        "fallback_years": fallback_years,
    }


def evaluate_forecast_benchmark(
    *,
    latitude: float,
    longitude: float,
    year: int | None,
    benchmark_years: int,
    tilt: float,
    panel_area: float,
    efficiency: float,
    cleanliness: str,
    shading: str,
    gamma: float,
    noct: float,
    ac_capacity_kw: float,
    training_years: int = 3,
    demo_mode: bool = False,
    demo_scenario_id: str | None = None,
) -> dict:
    evaluation_years = _resolve_evaluation_years(year, benchmark_years)
    system_loss_factor = compute_system_loss_factor(
        cleanliness=cleanliness,
        shading=shading,
    )

    actual_summaries_by_year = {
        evaluation_year: _build_actual_summary(
            latitude=latitude,
            longitude=longitude,
            year=evaluation_year,
            tilt=tilt,
            panel_area=panel_area,
            efficiency=efficiency,
            gamma=gamma,
            noct=noct,
            system_loss_factor=system_loss_factor,
            ac_capacity_kw=ac_capacity_kw,
            demo_mode=demo_mode,
            demo_scenario_id=demo_scenario_id,
        )
        for evaluation_year in evaluation_years
    }

    actual_summary_builder = lambda evaluation_year: actual_summaries_by_year[evaluation_year]
    benchmark_results = [
        _evaluate_approach(
            approach=approach,
            evaluation_years=evaluation_years,
            latitude=latitude,
            longitude=longitude,
            tilt=tilt,
            panel_area=panel_area,
            efficiency=efficiency,
            gamma=gamma,
            noct=noct,
            system_loss_factor=system_loss_factor,
            ac_capacity_kw=ac_capacity_kw,
            training_years=training_years,
            demo_mode=demo_mode,
            demo_scenario_id=demo_scenario_id,
            actual_summary_builder=actual_summary_builder,
        )
        for approach in ("physical", "ml", "naive")
    ]

    metadata = build_weather_profile_metadata(
        latitude=latitude,
        longitude=longitude,
        demo_mode=demo_mode,
        demo_scenario_id=demo_scenario_id,
    )
    return {
        "evaluation_years": evaluation_years,
        "benchmark_years_requested": benchmark_years,
        "training_window_years": training_years,
        "reference_note": BENCHMARK_REFERENCE_NOTE,
        "approaches": benchmark_results,
        **metadata,
    }
