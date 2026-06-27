from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DEFAULTS_PATH = Path(__file__).resolve().parents[2] / "shared" / "defaults.json"
_DEFAULTS: dict[str, Any] = json.loads(_DEFAULTS_PATH.read_text())

DEFAULT_TILT_DEGREES = float(_DEFAULTS["tilt_degrees"])
DEFAULT_PANEL_AREA_SQM = float(_DEFAULTS["panel_area_sqm"])
DEFAULT_PANEL_EFFICIENCY = float(_DEFAULTS["panel_efficiency"])
DEFAULT_CLEANLINESS = str(_DEFAULTS["cleanliness"])
DEFAULT_SHADING = str(_DEFAULTS["shading"])
DEFAULT_AC_CAPACITY_KW = float(_DEFAULTS["ac_capacity_kw"])
DEFAULT_TEMPERATURE_COEFFICIENT = float(_DEFAULTS["temperature_coefficient"])
DEFAULT_NOCT_C = float(_DEFAULTS["noct_c"])
DEFAULT_MODEL_TYPE = str(_DEFAULTS["model_type"])
DEFAULT_ELECTRICITY_PRICE_PER_KWH = float(_DEFAULTS["electricity_price_per_kwh"])
DEFAULT_CURRENCY = str(_DEFAULTS["currency"])
DEFAULT_SYSTEM_CAPEX = float(_DEFAULTS["system_capex"])
DEFAULT_TRAINING_YEARS = int(_DEFAULTS["training_years"])
DEFAULT_BENCHMARK_YEARS = int(_DEFAULTS["benchmark_years"])

MAX_PANEL_AREA_SQM = float(_DEFAULTS["max_panel_area_sqm"])
MAX_AC_CAPACITY_KW = float(_DEFAULTS["max_ac_capacity_kw"])
MAX_ELECTRICITY_PRICE_PER_KWH = float(_DEFAULTS["max_electricity_price_per_kwh"])
MAX_SYSTEM_CAPEX = float(_DEFAULTS["max_system_capex"])
MAX_SCENARIO_COMPARISON_SCENARIOS = int(_DEFAULTS["max_scenario_comparison_scenarios"])
