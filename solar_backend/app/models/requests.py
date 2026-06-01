from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ModelType = Literal["physical", "ml"]
CleanlinessLevel = Literal["clean", "normal", "dusty"]
ShadingLevel = Literal["none", "low", "medium", "high"]
CurrencyCode = Literal["USD", "EUR", "ILS"]
DEFAULT_ELECTRICITY_PRICE_PER_KWH = 0.48
DEFAULT_CURRENCY: CurrencyCode = "ILS"
MAX_PANEL_AREA_SQM = 100_000.0
MAX_AC_CAPACITY_KW = 50_000.0
MAX_ELECTRICITY_PRICE_PER_KWH = 100.0
MAX_SYSTEM_CAPEX = 1_000_000_000.0
MAX_SCENARIO_COMPARISON_SCENARIOS = 20


class BasePVRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    year: int | None = Field(default=None, ge=2000, le=2100)
    tilt: float = Field(default=30.0, ge=0.0, le=90.0)
    panel_area: float = Field(default=80.0, gt=0.0, le=MAX_PANEL_AREA_SQM)
    panel_efficiency: float = Field(default=0.20, gt=0.0, le=1.0)
    cleanliness: CleanlinessLevel = "normal"
    shading: ShadingLevel = "low"
    ac_capacity_kw: float = Field(default=15.0, gt=0.0, le=MAX_AC_CAPACITY_KW)
    gamma: float = Field(default=0.004, ge=0.0, le=0.02)
    noct: float = Field(default=45.0, ge=20.0, le=90.0)
    model_type: ModelType = "physical"
    electricity_price_per_kwh: float = Field(
        default=DEFAULT_ELECTRICITY_PRICE_PER_KWH,
        ge=0.0,
        le=MAX_ELECTRICITY_PRICE_PER_KWH,
    )
    currency: CurrencyCode = DEFAULT_CURRENCY
    system_capex: float = Field(default=25000.0, ge=0.0, le=MAX_SYSTEM_CAPEX)
    training_years: int = Field(default=3, ge=1, le=10)
    demo_mode: bool = False
    demo_scenario_id: str | None = None


class SimulationRequest(BasePVRequest):
    pass


class YearlyForecastRequest(BasePVRequest):
    pass


class AccuracyEvaluationRequest(BasePVRequest):
    pass


class BenchmarkEvaluationRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    year: int | None = Field(default=None, ge=2000, le=2100)
    benchmark_years: int = Field(default=3, ge=1, le=5)
    tilt: float = Field(default=30.0, ge=0.0, le=90.0)
    panel_area: float = Field(default=80.0, gt=0.0, le=MAX_PANEL_AREA_SQM)
    panel_efficiency: float = Field(default=0.20, gt=0.0, le=1.0)
    cleanliness: CleanlinessLevel = "normal"
    shading: ShadingLevel = "low"
    ac_capacity_kw: float = Field(default=15.0, gt=0.0, le=MAX_AC_CAPACITY_KW)
    gamma: float = Field(default=0.004, ge=0.0, le=0.02)
    noct: float = Field(default=45.0, ge=20.0, le=90.0)
    system_capex: float = Field(default=25000.0, ge=0.0, le=MAX_SYSTEM_CAPEX)
    training_years: int = Field(default=3, ge=1, le=10)
    demo_mode: bool = False
    demo_scenario_id: str | None = None


class ScenarioComparisonContext(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    year: int | None = Field(default=None, ge=2000, le=2100)
    model_type: ModelType = "physical"
    training_years: int = Field(default=3, ge=1, le=10)
    electricity_price_per_kwh: float = Field(
        default=DEFAULT_ELECTRICITY_PRICE_PER_KWH,
        ge=0.0,
        le=MAX_ELECTRICITY_PRICE_PER_KWH,
    )
    currency: CurrencyCode = DEFAULT_CURRENCY
    demo_mode: bool = False
    demo_scenario_id: str | None = None


class ScenarioComparisonScenario(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )

    name: str = Field(..., min_length=1, max_length=120)
    tilt: float = Field(default=30.0, ge=0.0, le=90.0)
    panel_area: float = Field(default=80.0, gt=0.0, le=MAX_PANEL_AREA_SQM)
    panel_efficiency: float = Field(default=0.20, gt=0.0, le=1.0)
    cleanliness: CleanlinessLevel = "normal"
    shading: ShadingLevel = "low"
    ac_capacity_kw: float = Field(default=15.0, gt=0.0, le=MAX_AC_CAPACITY_KW)
    gamma: float = Field(default=0.004, ge=0.0, le=0.02)
    noct: float = Field(default=45.0, ge=20.0, le=90.0)
    system_capex: float = Field(default=25000.0, ge=0.0, le=MAX_SYSTEM_CAPEX)


class ScenarioComparisonRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )

    context: ScenarioComparisonContext
    scenarios: list[ScenarioComparisonScenario] = Field(
        min_length=2,
        max_length=MAX_SCENARIO_COMPARISON_SCENARIOS,
    )
