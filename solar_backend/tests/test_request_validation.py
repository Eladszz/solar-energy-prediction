from __future__ import annotations

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from app.defaults import DEFAULT_SYSTEM_CAPEX
from app.models.requests import (
    AccuracyEvaluationRequest,
    BasePVRequest,
    BenchmarkEvaluationRequest,
    ScenarioComparisonContext,
    ScenarioComparisonRequest,
    ScenarioComparisonScenario,
    SimulationRequest,
    YearlyForecastRequest,
)
from app.routers import (
    accuracy_router,
    benchmark_router,
    health_router,
    scenario_comparison_router,
    simulate_router,
    yearly_forecast_router,
)
from app.validation import validation_exception_handler
from fastapi.exceptions import RequestValidationError

api_app = FastAPI()
api_app.add_exception_handler(RequestValidationError, validation_exception_handler)
api_app.include_router(health_router.router)
api_app.include_router(simulate_router.router, prefix="/simulate")
api_app.include_router(yearly_forecast_router.router, prefix="/forecast/yearly")
api_app.include_router(scenario_comparison_router.router, prefix="/scenarios")
api_app.include_router(accuracy_router.router, prefix="/evaluation")
api_app.include_router(benchmark_router.router, prefix="/evaluation")
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
            build_valid_comparison_scenario(name="Expanded Array", panel_area=90.0),
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
            }
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
    }


def assert_validation_error(response, field_name: str) -> None:
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"][-1] == field_name for error in errors)
    assert all("msg" in error and error["msg"] for error in errors)


class TestRequestModels:
    def test_request_models_accept_valid_payloads(self):
        payload = build_valid_payload()
        comparison_payload = build_valid_comparison_payload()

        base_request = BasePVRequest(**payload)
        simulation_request = SimulationRequest(**payload)
        yearly_request = YearlyForecastRequest(**payload)
        accuracy_request = AccuracyEvaluationRequest(**payload)
        benchmark_request = BenchmarkEvaluationRequest(
            **build_valid_benchmark_payload()
        )
        comparison_request = ScenarioComparisonRequest(**comparison_payload)

        assert base_request.model_dump() == simulation_request.model_dump()
        assert yearly_request.year == 2026
        assert accuracy_request.currency == "ILS"
        assert benchmark_request.benchmark_years == 3
        assert comparison_request.context.model_type == "physical"
        assert comparison_request.scenarios[1].name == "Expanded Array"

    def test_request_models_use_configured_default_capex(self):
        base_request = BasePVRequest(latitude=32.08, longitude=34.78)
        benchmark_request = BenchmarkEvaluationRequest(latitude=32.08, longitude=34.78)
        scenario = ScenarioComparisonScenario(name="Base System")

        assert base_request.system_capex == DEFAULT_SYSTEM_CAPEX
        assert benchmark_request.system_capex == DEFAULT_SYSTEM_CAPEX
        assert scenario.system_capex == DEFAULT_SYSTEM_CAPEX

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
            ("system_capex", -1.0),
            ("year", 1999),
            ("year", 2101),
            ("training_years", 0),
            ("training_years", 11),
            ("benchmark_years", 0),
            ("benchmark_years", 6),
        ],
    )
    def test_request_models_reject_invalid_numeric_bounds(
        self,
        field_name,
        value,
    ):
        payload = (
            build_valid_benchmark_payload(**{field_name: value})
            if field_name == "benchmark_years"
            else build_valid_payload(**{field_name: value})
        )

        with pytest.raises(ValidationError) as exc_info:
            if field_name == "benchmark_years":
                BenchmarkEvaluationRequest(**payload)
            else:
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

    def test_request_models_reject_non_finite_numbers(self):
        payload = build_valid_payload(panel_area=float("inf"))

        with pytest.raises(ValidationError) as exc_info:
            BasePVRequest(**payload)

        errors = exc_info.value.errors()
        assert any(error["loc"][-1] == "panel_area" for error in errors)

    def test_scenario_comparison_limits_number_of_scenarios(self):
        payload = build_valid_comparison_payload(
            scenarios=[
                build_valid_comparison_scenario(name=f"Variant {index}")
                for index in range(21)
            ]
        )

        with pytest.raises(ValidationError) as exc_info:
            ScenarioComparisonRequest(**payload)

        errors = exc_info.value.errors()
        assert any(error["loc"][-1] == "scenarios" for error in errors)


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
        response = client.post(
            "/evaluation/accuracy", json=build_valid_payload(year=2025)
        )

        assert response.status_code == 200
        assert response.json()["quality"] == "GOOD"

    @patch(
        "app.routers.accuracy_router.evaluate_yearly_accuracy",
        side_effect=AssertionError(
            "Business logic should not run for future accuracy years"
        ),
    )
    def test_accuracy_rejects_future_actual_year(self, _mock_evaluate):
        response = client.post(
            "/evaluation/accuracy", json=build_valid_payload(year=2100)
        )

        assert response.status_code == 422
        assert "completed year" in response.json()["detail"]

    @patch(
        "app.routers.benchmark_router.evaluate_forecast_benchmark",
        return_value=build_benchmark_response(),
    )
    def test_benchmark_accepts_valid_payload(self, _mock_evaluate):
        response = client.post(
            "/evaluation/benchmark", json=build_valid_benchmark_payload()
        )

        assert response.status_code == 200
        assert len(response.json()["approaches"]) == 3

    @patch(
        "app.routers.scenario_comparison_router.compare_yearly_scenarios",
        return_value=build_scenario_comparison_response(),
    )
    def test_scenario_comparison_accepts_valid_payloads(self, _mock_compare):
        response = client.post(
            "/scenarios/compare", json=build_valid_comparison_payload()
        )

        assert response.status_code == 200
        assert len(response.json()["results"]) == 1

    def test_api_rejects_raw_infinity_before_business_logic(self):
        raw_payload = (
            '{"latitude":32.08,"longitude":34.78,'
            '"panel_area":Infinity,"ac_capacity_kw":15.0}'
        )
        with patch(
            "app.routers.simulate_router.get_weather_forecast",
            side_effect=AssertionError(
                "Business logic should not run for invalid payloads"
            ),
        ):
            response = client.post(
                "/simulate",
                content=raw_payload,
                headers={"content-type": "application/json"},
            )

        assert_validation_error(response, "panel_area")

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
                "/evaluation/benchmark",
                build_valid_benchmark_payload(benchmark_years=9),
                "benchmark_years",
                "app.routers.benchmark_router.evaluate_forecast_benchmark",
            ),
            (
                "/scenarios/compare",
                build_valid_comparison_payload(
                    scenarios=[
                        build_valid_comparison_scenario(name="Base System"),
                        build_valid_comparison_scenario(
                            name="Invalid Variant",
                            shading="partial",
                        ),
                    ]
                ),
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
            side_effect=AssertionError(
                "Business logic should not run for invalid payloads"
            ),
        ):
            response = client.post(path, json=payload)

        assert_validation_error(response, field_name)

    def test_scenario_comparison_rejects_shared_context_fields_inside_scenario(self):
        payload = build_valid_comparison_payload(
            scenarios=[
                build_valid_comparison_scenario(name="Base System"),
                build_valid_comparison_scenario(
                    name="Bad Variant",
                    year=2027,
                ),
            ]
        )

        response = client.post("/scenarios/compare", json=payload)

        assert_validation_error(response, "year")
