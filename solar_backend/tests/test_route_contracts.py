from __future__ import annotations

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.models.responses import RootResponse
from app.routers import (
    accuracy_router,
    health_router,
    scenario_comparison_router,
    simulate_router,
    yearly_forecast_router,
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
        "electricity_price_per_kwh": 0.17,
        "currency": "USD",
        "training_years": 3,
    }
    payload.update(overrides)
    return payload


def build_financial_assumptions():
    return {
        "electricity_price_per_kwh": 0.17,
        "currency": "USD",
        "valuation_basis": "Estimated value from forecasted energy.",
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
        "actual_monthly_kwh": [98.3] * 12,
        "predicted_monthly_kwh": [100.0] * 12,
        "actual_monthly_estimated_value": [16.71] * 12,
        "predicted_monthly_estimated_value": [17.0] * 12,
        "mape_percent": 5.4,
        "yearly_mape_percent": 1.69,
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
        "results": [
            {
                "scenario": build_valid_payload(panel_area=80.0),
                "yearly_kwh": 1200.0,
                "monthly_kwh": [100.0] * 12,
                "yearly_estimated_value": 204.0,
                "monthly_estimated_value": [17.0] * 12,
                "financial_assumptions": build_financial_assumptions(),
                "deviation_percent": 0.0,
                "value_deviation_percent": 0.0,
            },
            {
                "scenario": build_valid_payload(panel_area=96.0, ac_capacity_kw=18.0),
                "yearly_kwh": 1440.0,
                "monthly_kwh": [120.0] * 12,
                "yearly_estimated_value": 244.8,
                "monthly_estimated_value": [20.4] * 12,
                "financial_assumptions": build_financial_assumptions(),
                "deviation_percent": 20.0,
                "value_deviation_percent": 20.0,
            },
        ],
    }


api_app = FastAPI(docs_url="/swagger", redoc_url="/redoc", openapi_url="/openapi.json")
api_app.include_router(health_router.router)
api_app.include_router(simulate_router.router, prefix="/simulate")
api_app.include_router(yearly_forecast_router.router, prefix="/forecast/yearly")
api_app.include_router(scenario_comparison_router.router, prefix="/scenarios")
api_app.include_router(accuracy_router.router, prefix="/evaluation")


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
    response = client.post("/evaluation/accuracy", json=build_valid_payload())

    assert response.status_code == 200
    assert response.json()["quality"] == "GOOD"


@patch(
    "app.routers.scenario_comparison_router.compare_yearly_scenarios",
    return_value=build_scenario_response(),
)
def test_documented_scenario_compare_path_works(_mock_compare):
    response = client.post(
        "/scenarios/compare",
        json=[
            build_valid_payload(panel_area=80.0),
            build_valid_payload(panel_area=96.0, ac_capacity_kw=18.0),
        ],
    )

    assert response.status_code == 200
    assert len(response.json()["results"]) == 2
