from __future__ import annotations

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.exceptions.domain_exceptions import (
    BenchmarkTrainingDataUnavailableError,
    EmptyScenarioComparisonError,
    ForecastTrainingDataUnavailableError,
)
from app.models.responses import RootResponse
from app.routers import (
    accuracy_router,
    benchmark_router,
    health_router,
    scenario_comparison_router,
    simulate_router,
    yearly_forecast_router,
)
from app.services.external_service import (
    ExternalServiceRateLimitError,
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)


def build_valid_payload(**overrides):
    payload = {
        "latitude": 32.08,
        "longitude": 34.78,
        "year": 2026,
        "tilt": 30.0,
        "panel_area": 80.0,
        "panel_efficiency": 0.20,
        "cleanliness": "normal",
        "shading": "low",
        "ac_capacity_kw": 15.0,
        "gamma": 0.004,
        "noct": 45.0,
        "model_type": "physical",
        "electricity_price_per_kwh": 0.48,
        "currency": "ILS",
        "system_capex": 60000.0,
        "training_years": 3,
    }
    payload.update(overrides)
    return payload


def build_valid_comparison_context(**overrides):
    payload = {
        "latitude": 32.08,
        "longitude": 34.78,
        "year": 2026,
        "model_type": "physical",
        "training_years": 3,
        "electricity_price_per_kwh": 0.48,
        "currency": "ILS",
        "demo_mode": False,
        "demo_scenario_id": None,
    }
    payload.update(overrides)
    return payload


def build_valid_benchmark_payload(**overrides):
    payload = {
        "latitude": 32.08,
        "longitude": 34.78,
        "year": 2025,
        "benchmark_years": 3,
        "tilt": 30.0,
        "panel_area": 80.0,
        "panel_efficiency": 0.20,
        "cleanliness": "normal",
        "shading": "low",
        "ac_capacity_kw": 15.0,
        "gamma": 0.004,
        "noct": 45.0,
        "training_years": 3,
        "demo_mode": False,
        "demo_scenario_id": None,
    }
    payload.update(overrides)
    return payload


def build_valid_comparison_scenario(**overrides):
    payload = {
        "name": "Base System",
        "tilt": 30.0,
        "panel_area": 80.0,
        "panel_efficiency": 0.20,
        "cleanliness": "normal",
        "shading": "low",
        "ac_capacity_kw": 15.0,
        "gamma": 0.004,
        "noct": 45.0,
        "system_capex": 60000.0,
    }
    payload.update(overrides)
    return payload


def build_valid_comparison_payload(**overrides):
    payload = {
        "context": build_valid_comparison_context(),
        "scenarios": [
            build_valid_comparison_scenario(name="Base System"),
            build_valid_comparison_scenario(
                name="Expanded Array",
                panel_area=96.0,
                ac_capacity_kw=18.0,
            ),
        ],
    }
    payload.update(overrides)
    return payload


def build_financial_assumptions():
    return {
        "electricity_price_per_kwh": 0.48,
        "currency": "ILS",
        "system_capex": 60000.0,
        "valuation_basis": "Estimated value from forecasted energy.",
        "annual_savings_basis": "Annual savings equal yearly value.",
        "payback_basis": "Simple payback = CAPEX / annual savings.",
    }


def build_yearly_response():
    return {
        "location": [32.08, 34.78],
        "forecast_year": 2026,
        "model_type_requested": "physical",
        "model_type_used": "physical",
        "weather_reference_year": 2025,
        "training_years_used": [],
        "monthly_kwh": [100.0] * 12,
        "yearly_kwh": 1200.0,
        "specific_yield_kwh_per_kwp": 75.0,
        "avg_daily_kwh": 3.3,
        "monthly_estimated_value": [17.0] * 12,
        "yearly_estimated_value": 204.0,
        "annual_savings": 204.0,
        "simple_payback_years": 122.5,
        "avg_monthly_estimated_value": 17.0,
        "financial_assumptions": build_financial_assumptions(),
        "fallback_reason": None,
        "ml_metadata": None,
    }


def build_accuracy_response():
    return {
        "year": 2025,
        "model_type_requested": "physical",
        "model_type_used": "physical",
        "weather_reference_year": 2024,
        "training_years_used": [],
        "fallback_reason": None,
        "actual_yearly_kwh": 1180.0,
        "predicted_yearly_kwh": 1200.0,
        "actual_yearly_estimated_value": 200.6,
        "predicted_yearly_estimated_value": 204.0,
        "actual_annual_savings": 200.6,
        "predicted_annual_savings": 204.0,
        "actual_simple_payback_years": 124.6,
        "predicted_simple_payback_years": 122.5,
        "actual_monthly_kwh": [98.3] * 12,
        "predicted_monthly_kwh": [100.0] * 12,
        "actual_monthly_estimated_value": [16.71] * 12,
        "predicted_monthly_estimated_value": [17.0] * 12,
        "monthly_mae_kwh": 1.7,
        "mape_percent": 5.4,
        "yearly_mae_kwh": 20.0,
        "yearly_mape_percent": 1.69,
        "bias_percent": 1.69,
        "bias_kwh": 20.0,
        "quality": "GOOD",
        "financial_assumptions": build_financial_assumptions(),
        "ml_metadata": None,
    }


def build_scenario_response():
    return {
        "year": 2026,
        "model_type_requested": "physical",
        "model_type_used": "physical",
        "weather_reference_year": 2025,
        "training_years_used": [],
        "fallback_reason": None,
        "baseline_yearly_kwh": 1200.0,
        "baseline_yearly_estimated_value": 204.0,
        "baseline_annual_savings": 204.0,
        "baseline_simple_payback_years": 122.5,
        "results": [
            {
                "scenario": build_valid_comparison_scenario(name="Base System"),
                "yearly_kwh": 1200.0,
                "monthly_kwh": [100.0] * 12,
                "yearly_estimated_value": 204.0,
                "annual_savings": 204.0,
                "simple_payback_years": 122.5,
                "payback_delta_years": 0.0,
                "monthly_estimated_value": [17.0] * 12,
                "financial_assumptions": build_financial_assumptions(),
                "deviation_percent": 0.0,
                "value_deviation_percent": 0.0,
            },
            {
                "scenario": build_valid_comparison_scenario(
                    name="Expanded Array",
                    panel_area=96.0,
                    ac_capacity_kw=18.0,
                ),
                "yearly_kwh": 1440.0,
                "monthly_kwh": [120.0] * 12,
                "yearly_estimated_value": 244.8,
                "annual_savings": 244.8,
                "simple_payback_years": 102.1,
                "payback_delta_years": -20.4,
                "monthly_estimated_value": [20.4] * 12,
                "financial_assumptions": build_financial_assumptions(),
                "deviation_percent": 20.0,
                "value_deviation_percent": 20.0,
            },
        ],
    }


def build_benchmark_response():
    return {
        "evaluation_years": [2023, 2024, 2025],
        "benchmark_years_requested": 3,
        "training_window_years": 3,
        "reference_note": "Benchmark note",
        "approaches": [
            {
                "approach": "physical",
                "label": "Physical",
                "description": "Physical baseline",
                "metrics": {
                    "monthly_mape_percent": 8.4,
                    "monthly_mae_kwh": 12.2,
                    "yearly_mape_percent": 5.3,
                    "yearly_mae_kwh": 81.4,
                    "bias_percent": -2.1,
                    "bias_kwh": -26.9,
                },
                "yearly_results": [
                    {
                        "year": 2025,
                        "actual_yearly_kwh": 1180.0,
                        "predicted_yearly_kwh": 1150.0,
                        "actual_monthly_kwh": [98.3] * 12,
                        "predicted_monthly_kwh": [95.8] * 12,
                        "yearly_mape_percent": 2.54,
                        "yearly_mae_kwh": 30.0,
                        "yearly_bias_kwh": -30.0,
                        "model_type_used": "physical",
                        "weather_reference_year": 2024,
                        "training_years_used": [],
                        "fallback_reason": None,
                    }
                ],
                "fallback_years": [],
            },
            {
                "approach": "ml",
                "label": "ML",
                "description": "ML baseline",
                "metrics": {
                    "monthly_mape_percent": 6.1,
                    "monthly_mae_kwh": 9.4,
                    "yearly_mape_percent": 3.8,
                    "yearly_mae_kwh": 60.1,
                    "bias_percent": 1.2,
                    "bias_kwh": 14.2,
                },
                "yearly_results": [
                    {
                        "year": 2025,
                        "actual_yearly_kwh": 1180.0,
                        "predicted_yearly_kwh": 1198.0,
                        "actual_monthly_kwh": [98.3] * 12,
                        "predicted_monthly_kwh": [99.8] * 12,
                        "yearly_mape_percent": 1.53,
                        "yearly_mae_kwh": 18.0,
                        "yearly_bias_kwh": 18.0,
                        "model_type_used": "ml",
                        "weather_reference_year": None,
                        "training_years_used": [2022, 2023, 2024],
                        "fallback_reason": None,
                    }
                ],
                "fallback_years": [],
            },
            {
                "approach": "naive",
                "label": "Naive",
                "description": "Naive baseline",
                "metrics": {
                    "monthly_mape_percent": 9.9,
                    "monthly_mae_kwh": 15.0,
                    "yearly_mape_percent": 6.1,
                    "yearly_mae_kwh": 94.5,
                    "bias_percent": -3.7,
                    "bias_kwh": -43.7,
                },
                "yearly_results": [
                    {
                        "year": 2025,
                        "actual_yearly_kwh": 1180.0,
                        "predicted_yearly_kwh": 1128.0,
                        "actual_monthly_kwh": [98.3] * 12,
                        "predicted_monthly_kwh": [94.0] * 12,
                        "yearly_mape_percent": 4.41,
                        "yearly_mae_kwh": 52.0,
                        "yearly_bias_kwh": -52.0,
                        "model_type_used": "naive",
                        "weather_reference_year": None,
                        "training_years_used": [2022, 2023, 2024],
                        "fallback_reason": None,
                    }
                ],
                "fallback_years": [],
            },
        ],
        "data_source": "live",
        "demo_scenario_id": None,
        "demo_scenario_name": None,
    }


api_app = FastAPI(docs_url="/swagger", redoc_url="/redoc", openapi_url="/openapi.json")
api_app.include_router(health_router.router)
api_app.include_router(simulate_router.router, prefix="/simulate")
api_app.include_router(yearly_forecast_router.router, prefix="/forecast/yearly")
api_app.include_router(scenario_comparison_router.router, prefix="/scenarios")
api_app.include_router(accuracy_router.router, prefix="/evaluation")
api_app.include_router(benchmark_router.router, prefix="/evaluation")


@api_app.get("/", response_model=RootResponse)
def root():
    return {"message": "Solar Forecasting Backend is running 🚀"}


client = TestClient(api_app)


def test_swagger_and_openapi_paths_match_backend_configuration():
    assert client.get("/swagger").status_code == 200
    assert client.get("/redoc").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 404


def test_openapi_uses_exact_mounted_paths_without_trailing_slashes():
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]

    assert "/" in paths
    assert "/health" in paths
    assert "/simulate" in paths
    assert "/forecast/yearly" in paths
    assert "/scenarios/compare" in paths
    assert "/evaluation/accuracy" in paths
    assert "/evaluation/benchmark" in paths
    assert "/simulate/" not in paths
    assert "/forecast/yearly/" not in paths


def test_openapi_exposes_named_response_models():
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]

    assert (
        paths["/simulate"]["post"]["responses"]["200"]["content"]["application/json"][
            "schema"
        ]["$ref"]
        == "#/components/schemas/SimulationResponse"
    )
    assert (
        paths["/forecast/yearly"]["post"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        == "#/components/schemas/YearlyForecastResponse"
    )
    assert (
        paths["/scenarios/compare"]["post"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        == "#/components/schemas/ScenarioComparisonResponse"
    )
    assert (
        paths["/evaluation/accuracy"]["post"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        == "#/components/schemas/AccuracyEvaluationResponse"
    )
    assert (
        paths["/evaluation/benchmark"]["post"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        == "#/components/schemas/BenchmarkEvaluationResponse"
    )
    assert (
        paths["/health"]["get"]["responses"]["200"]["content"]["application/json"][
            "schema"
        ]["$ref"]
        == "#/components/schemas/HealthResponse"
    )


@patch("app.routers.simulate_router.estimate_energy_value", return_value=12.5)
@patch(
    "app.routers.simulate_router.simulate_production_enhanced",
    return_value=[1.0] * 24,
)
@patch(
    "app.routers.simulate_router.get_weather_forecast",
    return_value={
        "timezone": "UTC",
        "hourly": {
            "time": [f"2026-01-01T{hour:02d}:00" for hour in range(24)],
            "shortwave_radiation": [600.0] * 24,
            "temperature_2m": [25.0] * 24,
        },
    },
)
@patch("app.routers.simulate_router.compute_system_loss_factor", return_value=0.87)
def test_documented_simulate_path_works_without_redirect(*_mocks):
    response = client.post(
        "/simulate",
        json=build_valid_payload(),
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert "location" not in response.headers


@patch(
    "app.routers.yearly_forecast_router.build_yearly_forecast_response",
    return_value=build_yearly_response(),
)
@patch(
    "app.routers.yearly_forecast_router.compute_system_loss_factor",
    return_value=0.87,
)
@patch(
    "app.routers.yearly_forecast_router.build_forecast_weather_profile",
    return_value=object(),
)
def test_documented_yearly_path_works_without_redirect(*_mocks):
    response = client.post(
        "/forecast/yearly",
        json=build_valid_payload(),
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert "location" not in response.headers


@patch(
    "app.routers.accuracy_router.evaluate_yearly_accuracy",
    return_value=build_accuracy_response(),
)
def test_documented_accuracy_path_works(_mock_evaluate):
    response = client.post("/evaluation/accuracy", json=build_valid_payload(year=2025))

    assert response.status_code == 200
    assert response.json()["quality"] == "GOOD"


@patch(
    "app.routers.benchmark_router.evaluate_forecast_benchmark",
    return_value=build_benchmark_response(),
)
def test_documented_benchmark_path_works(_mock_evaluate):
    response = client.post("/evaluation/benchmark", json=build_valid_benchmark_payload())

    assert response.status_code == 200
    assert len(response.json()["approaches"]) == 3


@patch(
    "app.routers.scenario_comparison_router.compare_yearly_scenarios",
    return_value=build_scenario_response(),
)
def test_documented_scenario_compare_path_works(_mock_compare):
    response = client.post(
        "/scenarios/compare",
        json=build_valid_comparison_payload(),
    )

    assert response.status_code == 200
    assert len(response.json()["results"]) == 2


@patch(
    "app.routers.simulate_router.get_weather_forecast",
    side_effect=ExternalServiceTimeoutError(
        provider="Weather forecast provider",
        user_message="Weather forecast provider timed out. Please try again in a moment.",
    ),
)
def test_simulate_returns_gateway_timeout_for_upstream_timeout(_mock_weather):
    response = client.post("/simulate", json=build_valid_payload())

    assert response.status_code == 504
    assert "timed out" in response.json()["detail"]


@patch(
    "app.routers.yearly_forecast_router.build_forecast_weather_profile",
    side_effect=ExternalServiceRateLimitError(
        provider="Historical weather provider",
        user_message="Historical weather provider is temporarily rate limited. Please retry in a minute.",
    ),
)
def test_yearly_returns_service_unavailable_for_rate_limit(_mock_profile):
    response = client.post("/forecast/yearly", json=build_valid_payload())

    assert response.status_code == 503
    assert "rate limited" in response.json()["detail"]


@patch(
    "app.routers.yearly_forecast_router.build_forecast_weather_profile",
    side_effect=ForecastTrainingDataUnavailableError(
        "No historical weather data was available for ML training"
    ),
)
def test_yearly_returns_bad_gateway_for_training_data_gap(_mock_profile):
    response = client.post("/forecast/yearly", json=build_valid_payload())

    assert response.status_code == 502
    assert "historical weather data" in response.json()["detail"]


@patch(
    "app.routers.accuracy_router.evaluate_yearly_accuracy",
    side_effect=ExternalServiceUnavailableError(
        provider="Historical weather provider",
        user_message="Historical weather provider is temporarily unavailable. Please try again shortly.",
    ),
)
def test_accuracy_returns_service_unavailable_for_upstream_outage(_mock_evaluate):
    response = client.post("/evaluation/accuracy", json=build_valid_payload(year=2025))

    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]


@patch(
    "app.routers.benchmark_router.evaluate_forecast_benchmark",
    side_effect=ExternalServiceUnavailableError(
        provider="Historical weather provider",
        user_message="Historical weather provider is temporarily unavailable. Please try again shortly.",
    ),
)
def test_benchmark_returns_service_unavailable_for_upstream_outage(_mock_evaluate):
    response = client.post("/evaluation/benchmark", json=build_valid_benchmark_payload())

    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]


@patch(
    "app.routers.benchmark_router.evaluate_forecast_benchmark",
    side_effect=BenchmarkTrainingDataUnavailableError(
        "No historical weather data was available for naive benchmark training"
    ),
)
def test_benchmark_returns_bad_gateway_for_training_data_gap(_mock_evaluate):
    response = client.post("/evaluation/benchmark", json=build_valid_benchmark_payload())

    assert response.status_code == 502
    assert "naive benchmark training" in response.json()["detail"]


@patch(
    "app.routers.scenario_comparison_router.compare_yearly_scenarios",
    side_effect=EmptyScenarioComparisonError("At least one scenario is required"),
)
def test_scenario_compare_returns_bad_request_for_domain_error(_mock_compare):
    response = client.post(
        "/scenarios/compare",
        json=build_valid_comparison_payload(),
    )

    assert response.status_code == 400
    assert "At least one scenario" in response.json()["detail"]
