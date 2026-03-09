from __future__ import annotations

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from app.models.requests import (
    AccuracyEvaluationRequest,
    BasePVRequest,
    SimulationRequest,
    YearlyForecastRequest,
)
from app.routers import (
    accuracy_router,
    health_router,
    scenario_comparison_router,
    simulate_router,
    yearly_forecast_router,
)

api_app = FastAPI()
api_app.include_router(health_router.router)
api_app.include_router(simulate_router.router, prefix="/simulate")
api_app.include_router(yearly_forecast_router.router, prefix="/forecast/yearly")
api_app.include_router(scenario_comparison_router.router, prefix="/scenarios")
api_app.include_router(accuracy_router.router, prefix="/evaluation")
client = TestClient(api_app)


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


def build_scenario_comparison_response():
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
            }
        ],
    }


def assert_validation_error(response, field_name: str) -> None:
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"][-1] == field_name for error in errors)
    assert all("msg" in error and error["msg"] for error in errors)


class TestRequestModels:
    def test_request_models_accept_valid_payloads(self):
        payload = build_valid_payload()

        base_request = BasePVRequest(**payload)
        simulation_request = SimulationRequest(**payload)
        yearly_request = YearlyForecastRequest(**payload)
        accuracy_request = AccuracyEvaluationRequest(**payload)

        assert base_request.model_dump() == simulation_request.model_dump()
        assert yearly_request.year == 2026
        assert accuracy_request.currency == "USD"

    @pytest.mark.parametrize(
        ("field_name", "value"),
        [
            ("latitude", -90.1),
            ("latitude", 90.1),
            ("longitude", -180.1),
            ("longitude", 180.1),
            ("tilt", -0.1),
            ("tilt", 90.1),
            ("panel_area", 0.0),
            ("panel_efficiency", 0.0),
            ("panel_efficiency", 1.01),
            ("ac_capacity_kw", 0.0),
            ("year", 1999),
            ("year", 2101),
            ("training_years", 0),
            ("training_years", 11),
        ],
    )
    def test_request_models_reject_invalid_numeric_bounds(
        self,
        field_name,
        value,
    ):
        payload = build_valid_payload(**{field_name: value})

        with pytest.raises(ValidationError) as exc_info:
            BasePVRequest(**payload)

        errors = exc_info.value.errors()
        assert any(error["loc"][-1] == field_name for error in errors)
        assert all("msg" in error and error["msg"] for error in errors)

    @pytest.mark.parametrize(
        ("field_name", "value"),
        [
            ("cleanliness", "dirty"),
            ("shading", "partial"),
            ("currency", "GBP"),
            ("model_type", "hybrid"),
        ],
    )
    def test_request_models_reject_invalid_literal_values(self, field_name, value):
        payload = build_valid_payload(**{field_name: value})

        with pytest.raises(ValidationError) as exc_info:
            BasePVRequest(**payload)

        errors = exc_info.value.errors()
        assert any(error["loc"][-1] == field_name for error in errors)
        assert all("msg" in error and error["msg"] for error in errors)

    def test_request_models_forbid_extra_fields(self):
        payload = build_valid_payload(unexpected_field="nope")

        with pytest.raises(ValidationError) as exc_info:
            BasePVRequest(**payload)

        errors = exc_info.value.errors()
        assert any(error["loc"][-1] == "unexpected_field" for error in errors)


class TestApiValidation:
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
    @patch(
        "app.routers.simulate_router.compute_system_loss_factor",
        return_value=0.87,
    )
    def test_simulate_accepts_valid_payload(self, *_mocks):
        response = client.post("/simulate", json=build_valid_payload())

        assert response.status_code == 200
        assert response.json()["daily_kwh"] == 24.0

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
    def test_yearly_accepts_valid_payload(self, *_mocks):
        response = client.post("/forecast/yearly", json=build_valid_payload())

        assert response.status_code == 200
        assert response.json()["yearly_kwh"] == 1200.0

    @patch(
        "app.routers.accuracy_router.evaluate_yearly_accuracy",
        return_value=build_accuracy_response(),
    )
    def test_accuracy_accepts_valid_payload(self, _mock_evaluate):
        response = client.post("/evaluation/accuracy", json=build_valid_payload())

        assert response.status_code == 200
        assert response.json()["quality"] == "GOOD"

    @patch(
        "app.routers.scenario_comparison_router.compare_yearly_scenarios",
        return_value=build_scenario_comparison_response(),
    )
    def test_scenario_comparison_accepts_valid_payloads(self, _mock_compare):
        scenarios = [
            build_valid_payload(panel_area=80.0),
            build_valid_payload(panel_area=90.0),
        ]

        response = client.post("/scenarios/compare", json=scenarios)

        assert response.status_code == 200
        assert len(response.json()["results"]) == 1

    @pytest.mark.parametrize(
        ("path", "payload", "field_name", "patch_target"),
        [
            (
                "/simulate",
                build_valid_payload(latitude=95.0),
                "latitude",
                "app.routers.simulate_router.get_weather_forecast",
            ),
            (
                "/forecast/yearly",
                build_valid_payload(panel_area=0.0),
                "panel_area",
                "app.routers.yearly_forecast_router.build_forecast_weather_profile",
            ),
            (
                "/evaluation/accuracy",
                build_valid_payload(currency="GBP"),
                "currency",
                "app.routers.accuracy_router.evaluate_yearly_accuracy",
            ),
            (
                "/scenarios/compare",
                [
                    build_valid_payload(),
                    build_valid_payload(shading="partial"),
                ],
                "shading",
                "app.routers.scenario_comparison_router.compare_yearly_scenarios",
            ),
        ],
    )
    def test_api_rejects_invalid_payloads_before_business_logic(
        self,
        path,
        payload,
        field_name,
        patch_target,
    ):
        with patch(
            patch_target,
            side_effect=AssertionError("Business logic should not run for invalid payloads"),
        ):
            response = client.post(path, json=payload)

        assert_validation_error(response, field_name)
