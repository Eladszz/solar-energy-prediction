from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ModelType = Literal["physical", "ml"]
CleanlinessLevel = Literal["clean", "normal", "dusty"]
ShadingLevel = Literal["none", "low", "medium", "high"]
CurrencyCode = Literal["USD", "EUR", "ILS"]


class BasePVRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    year: int | None = Field(default=None, ge=2000, le=2100)
    tilt: float = Field(default=30.0, ge=0.0, le=90.0)
    panel_area: float = Field(default=80.0, gt=0.0)
    panel_efficiency: float = Field(default=0.20, gt=0.0, le=1.0)
    cleanliness: CleanlinessLevel = "normal"
    shading: ShadingLevel = "low"
    ac_capacity_kw: float = Field(default=15.0, gt=0.0)
    gamma: float = 0.004
    noct: float = 45.0
    model_type: ModelType = "physical"
    electricity_price_per_kwh: float = Field(default=0.17, ge=0.0)
    currency: CurrencyCode = "USD"
    system_capex: float = Field(default=25000.0, ge=0.0)
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
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    year: int | None = Field(default=None, ge=2000, le=2100)
    benchmark_years: int = Field(default=3, ge=1, le=5)
    tilt: float = Field(default=30.0, ge=0.0, le=90.0)
    panel_area: float = Field(default=80.0, gt=0.0)
    panel_efficiency: float = Field(default=0.20, gt=0.0, le=1.0)
    cleanliness: CleanlinessLevel = "normal"
    shading: ShadingLevel = "low"
    ac_capacity_kw: float = Field(default=15.0, gt=0.0)
    gamma: float = 0.004
    noct: float = 45.0
    system_capex: float = Field(default=25000.0, ge=0.0)
    training_years: int = Field(default=3, ge=1, le=10)
    demo_mode: bool = False
    demo_scenario_id: str | None = None


class ScenarioComparisonContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    year: int | None = Field(default=None, ge=2000, le=2100)
    model_type: ModelType = "physical"
    training_years: int = Field(default=3, ge=1, le=10)
    electricity_price_per_kwh: float = Field(default=0.17, ge=0.0)
    currency: CurrencyCode = "USD"
    demo_mode: bool = False
    demo_scenario_id: str | None = None


class ScenarioComparisonScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=120)
    tilt: float = Field(default=30.0, ge=0.0, le=90.0)
    panel_area: float = Field(default=80.0, gt=0.0)
    panel_efficiency: float = Field(default=0.20, gt=0.0, le=1.0)
    cleanliness: CleanlinessLevel = "normal"
    shading: ShadingLevel = "low"
    ac_capacity_kw: float = Field(default=15.0, gt=0.0)
    gamma: float = 0.004
    noct: float = 45.0
    system_capex: float = Field(default=25000.0, ge=0.0)


class ScenarioComparisonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context: ScenarioComparisonContext
    scenarios: list[ScenarioComparisonScenario] = Field(min_length=2)
