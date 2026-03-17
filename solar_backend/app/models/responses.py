from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.requests import (
    CurrencyCode,
    ModelType,
    ScenarioComparisonScenario,
)


class ApiResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(ApiResponseModel):
    status: Literal["ok"]


class RootResponse(ApiResponseModel):
    message: str


class FinancialAssumptions(ApiResponseModel):
    electricity_price_per_kwh: float
    currency: CurrencyCode
    system_capex: float
    valuation_basis: str
    annual_savings_basis: str
    payback_basis: str


class SimulationResponse(ApiResponseModel):
    location: list[float] = Field(min_length=2, max_length=2)
    system_loss_factor: float
    hourly_ac_kw: list[float]
    avg_kw: float
    daily_kwh: float
    estimated_daily_value: float
    financial_assumptions: FinancialAssumptions
    timezone: str
    hourly_time: list[str]
    data_source: Literal["live", "demo"] = "live"
    demo_scenario_id: str | None = None
    demo_scenario_name: str | None = None


class YearlyForecastResponse(ApiResponseModel):
    location: list[float] = Field(min_length=2, max_length=2)
    forecast_year: int
    model_type_requested: ModelType
    model_type_used: ModelType
    weather_reference_year: int | None = None
    training_years_used: list[int]
    monthly_kwh: list[float]
    yearly_kwh: float
    specific_yield_kwh_per_kwp: float
    avg_daily_kwh: float
    monthly_estimated_value: list[float]
    yearly_estimated_value: float
    annual_savings: float
    simple_payback_years: float | None = None
    avg_monthly_estimated_value: float
    financial_assumptions: FinancialAssumptions
    fallback_reason: str | None = None
    ml_metadata: dict[str, Any] | None = None
    data_source: Literal["live", "demo"] = "live"
    demo_scenario_id: str | None = None
    demo_scenario_name: str | None = None


QualityLabel = Literal["EXCELLENT", "GOOD", "POOR"]


class AccuracyEvaluationResponse(ApiResponseModel):
    year: int
    model_type_requested: ModelType
    model_type_used: ModelType
    weather_reference_year: int | None = None
    training_years_used: list[int]
    fallback_reason: str | None = None
    actual_yearly_kwh: float
    predicted_yearly_kwh: float
    actual_yearly_estimated_value: float
    predicted_yearly_estimated_value: float
    actual_annual_savings: float
    predicted_annual_savings: float
    actual_simple_payback_years: float | None = None
    predicted_simple_payback_years: float | None = None
    actual_monthly_kwh: list[float]
    predicted_monthly_kwh: list[float]
    actual_monthly_estimated_value: list[float]
    predicted_monthly_estimated_value: list[float]
    mape_percent: float
    yearly_mape_percent: float
    quality: QualityLabel
    financial_assumptions: FinancialAssumptions
    ml_metadata: dict[str, Any] | None = None
    data_source: Literal["live", "demo"] = "live"
    demo_scenario_id: str | None = None
    demo_scenario_name: str | None = None


BenchmarkApproachType = Literal["physical", "ml", "naive"]


class BenchmarkMetrics(ApiResponseModel):
    monthly_mape_percent: float
    monthly_mae_kwh: float
    yearly_mape_percent: float
    yearly_mae_kwh: float
    bias_percent: float
    bias_kwh: float


class BenchmarkYearResult(ApiResponseModel):
    year: int
    actual_yearly_kwh: float
    predicted_yearly_kwh: float
    actual_monthly_kwh: list[float]
    predicted_monthly_kwh: list[float]
    yearly_mape_percent: float
    yearly_mae_kwh: float
    yearly_bias_kwh: float
    model_type_used: BenchmarkApproachType
    weather_reference_year: int | None = None
    training_years_used: list[int]
    fallback_reason: str | None = None


class BenchmarkApproachResult(ApiResponseModel):
    approach: BenchmarkApproachType
    label: str
    description: str
    metrics: BenchmarkMetrics
    yearly_results: list[BenchmarkYearResult] = Field(min_length=1)
    fallback_years: list[int] = Field(default_factory=list)


class BenchmarkEvaluationResponse(ApiResponseModel):
    evaluation_years: list[int] = Field(min_length=1)
    benchmark_years_requested: int
    training_window_years: int
    reference_note: str
    approaches: list[BenchmarkApproachResult] = Field(min_length=3, max_length=3)
    data_source: Literal["live", "demo"] = "live"
    demo_scenario_id: str | None = None
    demo_scenario_name: str | None = None


class ScenarioComparisonResult(ApiResponseModel):
    scenario: ScenarioComparisonScenario
    yearly_kwh: float
    monthly_kwh: list[float]
    yearly_estimated_value: float
    annual_savings: float
    simple_payback_years: float | None = None
    payback_delta_years: float | None = None
    monthly_estimated_value: list[float]
    financial_assumptions: FinancialAssumptions
    deviation_percent: float
    value_deviation_percent: float


class ScenarioComparisonResponse(ApiResponseModel):
    year: int
    model_type_requested: ModelType
    model_type_used: ModelType
    weather_reference_year: int | None = None
    training_years_used: list[int]
    fallback_reason: str | None = None
    baseline_yearly_kwh: float
    baseline_yearly_estimated_value: float
    baseline_annual_savings: float
    baseline_simple_payback_years: float | None = None
    results: list[ScenarioComparisonResult]
    data_source: Literal["live", "demo"] = "live"
    demo_scenario_id: str | None = None
    demo_scenario_name: str | None = None
