from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from app.defaults import (
    DEFAULT_AC_CAPACITY_KW,
    DEFAULT_BENCHMARK_YEARS,
    DEFAULT_CLEANLINESS,
    DEFAULT_CURRENCY,
    DEFAULT_ELECTRICITY_PRICE_PER_KWH,
    DEFAULT_MODEL_TYPE,
    DEFAULT_NOCT_C,
    DEFAULT_PANEL_AREA_SQM,
    DEFAULT_PANEL_EFFICIENCY,
    DEFAULT_SHADING,
    DEFAULT_SYSTEM_CAPEX,
    DEFAULT_TEMPERATURE_COEFFICIENT,
    DEFAULT_TILT_DEGREES,
    DEFAULT_TRAINING_YEARS,
    MAX_AC_CAPACITY_KW,
    MAX_ELECTRICITY_PRICE_PER_KWH,
    MAX_PANEL_AREA_SQM,
    MAX_SCENARIO_COMPARISON_SCENARIOS,
    MAX_SYSTEM_CAPEX,
)

ModelType = Literal["physical", "ml"]
CleanlinessLevel = Literal["clean", "normal", "dusty"]
ShadingLevel = Literal["none", "low", "medium", "high"]
CurrencyCode = Literal["USD", "EUR", "ILS"]


class BasePVRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    year: int | None = Field(default=None, ge=2000, le=2100)
    tilt: float = Field(default=DEFAULT_TILT_DEGREES, ge=0.0, le=90.0)
    panel_area: float = Field(
        default=DEFAULT_PANEL_AREA_SQM, gt=0.0, le=MAX_PANEL_AREA_SQM
    )
    panel_efficiency: float = Field(default=DEFAULT_PANEL_EFFICIENCY, gt=0.0, le=1.0)
    cleanliness: CleanlinessLevel = DEFAULT_CLEANLINESS
    shading: ShadingLevel = DEFAULT_SHADING
    ac_capacity_kw: float = Field(
        default=DEFAULT_AC_CAPACITY_KW, gt=0.0, le=MAX_AC_CAPACITY_KW
    )
    gamma: float = Field(default=DEFAULT_TEMPERATURE_COEFFICIENT, ge=0.0, le=0.02)
    noct: float = Field(default=DEFAULT_NOCT_C, ge=20.0, le=90.0)
    model_type: ModelType = DEFAULT_MODEL_TYPE
    electricity_price_per_kwh: float = Field(
        default=DEFAULT_ELECTRICITY_PRICE_PER_KWH,
        ge=0.0,
        le=MAX_ELECTRICITY_PRICE_PER_KWH,
    )
    currency: CurrencyCode = DEFAULT_CURRENCY
    system_capex: float = Field(
        default=DEFAULT_SYSTEM_CAPEX, ge=0.0, le=MAX_SYSTEM_CAPEX
    )
    training_years: int = Field(default=DEFAULT_TRAINING_YEARS, ge=1, le=10)


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
    benchmark_years: int = Field(default=DEFAULT_BENCHMARK_YEARS, ge=1, le=5)
    tilt: float = Field(default=DEFAULT_TILT_DEGREES, ge=0.0, le=90.0)
    panel_area: float = Field(
        default=DEFAULT_PANEL_AREA_SQM, gt=0.0, le=MAX_PANEL_AREA_SQM
    )
    panel_efficiency: float = Field(default=DEFAULT_PANEL_EFFICIENCY, gt=0.0, le=1.0)
    cleanliness: CleanlinessLevel = DEFAULT_CLEANLINESS
    shading: ShadingLevel = DEFAULT_SHADING
    ac_capacity_kw: float = Field(
        default=DEFAULT_AC_CAPACITY_KW, gt=0.0, le=MAX_AC_CAPACITY_KW
    )
    gamma: float = Field(default=DEFAULT_TEMPERATURE_COEFFICIENT, ge=0.0, le=0.02)
    noct: float = Field(default=DEFAULT_NOCT_C, ge=20.0, le=90.0)
    system_capex: float = Field(
        default=DEFAULT_SYSTEM_CAPEX, ge=0.0, le=MAX_SYSTEM_CAPEX
    )
    training_years: int = Field(default=DEFAULT_TRAINING_YEARS, ge=1, le=10)


class ScenarioComparisonContext(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    year: int | None = Field(default=None, ge=2000, le=2100)
    model_type: ModelType = DEFAULT_MODEL_TYPE
    training_years: int = Field(default=DEFAULT_TRAINING_YEARS, ge=1, le=10)
    electricity_price_per_kwh: float = Field(
        default=DEFAULT_ELECTRICITY_PRICE_PER_KWH,
        ge=0.0,
        le=MAX_ELECTRICITY_PRICE_PER_KWH,
    )
    currency: CurrencyCode = DEFAULT_CURRENCY


class ScenarioComparisonScenario(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )

    name: str = Field(..., min_length=1, max_length=120)
    tilt: float = Field(default=DEFAULT_TILT_DEGREES, ge=0.0, le=90.0)
    panel_area: float = Field(
        default=DEFAULT_PANEL_AREA_SQM, gt=0.0, le=MAX_PANEL_AREA_SQM
    )
    panel_efficiency: float = Field(default=DEFAULT_PANEL_EFFICIENCY, gt=0.0, le=1.0)
    cleanliness: CleanlinessLevel = DEFAULT_CLEANLINESS
    shading: ShadingLevel = DEFAULT_SHADING
    ac_capacity_kw: float = Field(
        default=DEFAULT_AC_CAPACITY_KW, gt=0.0, le=MAX_AC_CAPACITY_KW
    )
    gamma: float = Field(default=DEFAULT_TEMPERATURE_COEFFICIENT, ge=0.0, le=0.02)
    noct: float = Field(default=DEFAULT_NOCT_C, ge=20.0, le=90.0)
    system_capex: float = Field(
        default=DEFAULT_SYSTEM_CAPEX, ge=0.0, le=MAX_SYSTEM_CAPEX
    )


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
