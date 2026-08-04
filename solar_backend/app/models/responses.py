from pydantic import BaseModel, ConfigDict, Field

from app.models.requests import ScenarioComparisonScenario


class ApiResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(ApiResponseModel):
    status: str


class RootResponse(ApiResponseModel):
    message: str


class FinancialAssumptions(ApiResponseModel):
    electricity_price_per_kwh: float
    currency: str
    system_capex: float
    valuation_basis: str
    annual_savings_basis: str
    payback_basis: str


class SimulationResponse(ApiResponseModel):
    location: list[float] = Field(min_length=2, max_length=2)
    production_model: str
    weather_source: str
    system_loss_factor: float
    hourly_ac_kw: list[float]
    avg_kw: float
    daily_kwh: float
    estimated_daily_value: float
    financial_assumptions: FinancialAssumptions
    timezone: str
    hourly_time: list[str]


class YearlyForecastResponse(ApiResponseModel):
    location: list[float] = Field(min_length=2, max_length=2)
    requested_forecast_year: int
    production_model: str
    weather_source: str
    weather_reference_year: int
    monthly_kwh: list[float] = Field(min_length=12, max_length=12)
    yearly_kwh: float
    specific_yield_kwh_per_kwp: float
    avg_daily_kwh: float
    monthly_estimated_value: list[float] = Field(min_length=12, max_length=12)
    yearly_estimated_value: float
    annual_savings: float
    simple_payback_years: float | None = None
    avg_monthly_estimated_value: float
    financial_assumptions: FinancialAssumptions
    fallback_reason: str | None = None


class ScenarioComparisonResult(ApiResponseModel):
    scenario: ScenarioComparisonScenario
    yearly_kwh: float
    monthly_kwh: list[float] = Field(min_length=12, max_length=12)
    yearly_estimated_value: float
    annual_savings: float
    simple_payback_years: float | None = None
    payback_delta_years: float | None = None
    monthly_estimated_value: list[float] = Field(min_length=12, max_length=12)
    financial_assumptions: FinancialAssumptions
    deviation_percent: float
    value_deviation_percent: float


class ScenarioComparisonResponse(ApiResponseModel):
    requested_forecast_year: int
    production_model: str
    weather_source: str
    weather_reference_year: int
    fallback_reason: str | None = None
    baseline_yearly_kwh: float
    baseline_yearly_estimated_value: float
    baseline_annual_savings: float
    baseline_simple_payback_years: float | None = None
    results: list[ScenarioComparisonResult]
