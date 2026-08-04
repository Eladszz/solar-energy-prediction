from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.defaults import (
    DEFAULT_AC_CAPACITY_KW,
    DEFAULT_CLEANLINESS,
    DEFAULT_CURRENCY,
    DEFAULT_ELECTRICITY_PRICE_PER_KWH,
    DEFAULT_NOCT_C,
    DEFAULT_PANEL_AREA_SQM,
    DEFAULT_PANEL_EFFICIENCY,
    DEFAULT_SHADING,
    DEFAULT_SYSTEM_CAPEX,
    DEFAULT_TEMPERATURE_COEFFICIENT,
    DEFAULT_TILT_DEGREES,
    MAX_AC_CAPACITY_KW,
    MAX_ELECTRICITY_PRICE_PER_KWH,
    MAX_PANEL_AREA_SQM,
    MAX_SCENARIO_COMPARISON_SCENARIOS,
    MAX_SYSTEM_CAPEX,
)

CleanlinessLevel = str
ShadingLevel = str
CurrencyCode = str


class StrictRequestModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", allow_inf_nan=False, hide_input_in_errors=True
    )


class BasePVRequest(StrictRequestModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    year: int | None = Field(default=None, ge=2000, le=2100)
    tilt: float = Field(default=DEFAULT_TILT_DEGREES, ge=0.0, le=90.0)
    panel_area: float = Field(
        default=DEFAULT_PANEL_AREA_SQM, gt=0.0, le=MAX_PANEL_AREA_SQM
    )
    panel_efficiency: float = Field(default=DEFAULT_PANEL_EFFICIENCY, gt=0.0, le=1.0)
    cleanliness: str = Field(
        default=DEFAULT_CLEANLINESS, pattern="^(clean|normal|dusty)$"
    )
    shading: str = Field(default=DEFAULT_SHADING, pattern="^(none|low|medium|high)$")
    ac_capacity_kw: float = Field(
        default=DEFAULT_AC_CAPACITY_KW, gt=0.0, le=MAX_AC_CAPACITY_KW
    )
    gamma: float = Field(default=DEFAULT_TEMPERATURE_COEFFICIENT, ge=0.0, le=0.02)
    noct: float = Field(default=DEFAULT_NOCT_C, ge=20.0, le=90.0)
    electricity_price_per_kwh: float = Field(
        default=DEFAULT_ELECTRICITY_PRICE_PER_KWH,
        ge=0.0,
        le=MAX_ELECTRICITY_PRICE_PER_KWH,
    )
    currency: str = Field(default=DEFAULT_CURRENCY, pattern="^(USD|EUR|ILS)$")
    system_capex: float = Field(
        default=DEFAULT_SYSTEM_CAPEX, ge=0.0, le=MAX_SYSTEM_CAPEX
    )


class SimulationRequest(BasePVRequest):
    pass


class YearlyForecastRequest(BasePVRequest):
    pass


class ScenarioComparisonContext(StrictRequestModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    year: int | None = Field(default=None, ge=2000, le=2100)
    electricity_price_per_kwh: float = Field(
        default=DEFAULT_ELECTRICITY_PRICE_PER_KWH,
        ge=0.0,
        le=MAX_ELECTRICITY_PRICE_PER_KWH,
    )
    currency: str = Field(default=DEFAULT_CURRENCY, pattern="^(USD|EUR|ILS)$")


class ScenarioComparisonScenario(StrictRequestModel):
    name: str = Field(..., min_length=1, max_length=120)
    tilt: float = Field(default=DEFAULT_TILT_DEGREES, ge=0.0, le=90.0)
    panel_area: float = Field(
        default=DEFAULT_PANEL_AREA_SQM, gt=0.0, le=MAX_PANEL_AREA_SQM
    )
    panel_efficiency: float = Field(default=DEFAULT_PANEL_EFFICIENCY, gt=0.0, le=1.0)
    cleanliness: str = Field(
        default=DEFAULT_CLEANLINESS, pattern="^(clean|normal|dusty)$"
    )
    shading: str = Field(default=DEFAULT_SHADING, pattern="^(none|low|medium|high)$")
    ac_capacity_kw: float = Field(
        default=DEFAULT_AC_CAPACITY_KW, gt=0.0, le=MAX_AC_CAPACITY_KW
    )
    gamma: float = Field(default=DEFAULT_TEMPERATURE_COEFFICIENT, ge=0.0, le=0.02)
    noct: float = Field(default=DEFAULT_NOCT_C, ge=20.0, le=90.0)
    system_capex: float = Field(
        default=DEFAULT_SYSTEM_CAPEX, ge=0.0, le=MAX_SYSTEM_CAPEX
    )


class ScenarioComparisonRequest(StrictRequestModel):
    context: ScenarioComparisonContext
    scenarios: list[ScenarioComparisonScenario] = Field(
        min_length=2, max_length=MAX_SCENARIO_COMPARISON_SCENARIOS
    )

    @model_validator(mode="after")
    def reject_duplicate_names(self) -> "ScenarioComparisonRequest":
        normalized = [scenario.name.strip().casefold() for scenario in self.scenarios]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Scenario names must be unique.")
        return self
