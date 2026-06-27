from __future__ import annotations

from typing import Any, Mapping, TypeAlias, TypedDict

import pandas as pd


class PVRequestPayload(TypedDict):
    latitude: float
    longitude: float
    year: int
    tilt: int
    panel_area: float
    panel_efficiency: float
    cleanliness: str
    shading: str
    ac_capacity_kw: float
    gamma: float
    noct: float
    model_type: str
    electricity_price_per_kwh: float
    currency: str
    system_capex: float
    training_years: int


class ScenarioComparisonContextPayload(TypedDict):
    latitude: float
    longitude: float
    year: int
    model_type: str
    training_years: int
    electricity_price_per_kwh: float
    currency: str


class ScenarioComparisonScenarioPayload(TypedDict):
    name: str
    tilt: int
    panel_area: float
    panel_efficiency: float
    cleanliness: str
    shading: str
    ac_capacity_kw: float
    gamma: float
    noct: float
    system_capex: float


class ScenarioComparisonRequestPayload(TypedDict):
    context: ScenarioComparisonContextPayload
    scenarios: list[ScenarioComparisonScenarioPayload]


class BenchmarkEvaluationPayload(TypedDict):
    latitude: float
    longitude: float
    year: int
    benchmark_years: int
    tilt: int
    panel_area: float
    panel_efficiency: float
    cleanliness: str
    shading: str
    ac_capacity_kw: float
    gamma: float
    noct: float
    training_years: int


ApiPayload: TypeAlias = (
    PVRequestPayload
    | BenchmarkEvaluationPayload
    | ScenarioComparisonRequestPayload
    | dict[str, Any]
    | list[PVRequestPayload]
    | list[dict[str, Any]]
)


def build_common_payload(
    latitude: float,
    longitude: float,
    year: int,
    tilt: int,
    panel_area: float,
    panel_efficiency: float,
    cleanliness: str,
    shading: str,
    ac_capacity_kw: float,
    gamma: float,
    noct: float,
    model_type: str,
    electricity_price_per_kwh: float,
    currency: str,
    system_capex: float,
    training_years: int,
) -> PVRequestPayload:
    return {
        "latitude": latitude,
        "longitude": longitude,
        "year": year,
        "tilt": tilt,
        "panel_area": panel_area,
        "panel_efficiency": panel_efficiency,
        "cleanliness": cleanliness,
        "shading": shading,
        "ac_capacity_kw": ac_capacity_kw,
        "gamma": gamma,
        "noct": noct,
        "model_type": model_type,
        "electricity_price_per_kwh": electricity_price_per_kwh,
        "currency": currency,
        "system_capex": system_capex,
        "training_years": training_years,
    }


def build_scenario_comparison_context(
    base_payload: PVRequestPayload,
) -> ScenarioComparisonContextPayload:
    return {
        "latitude": base_payload["latitude"],
        "longitude": base_payload["longitude"],
        "year": base_payload["year"],
        "model_type": base_payload["model_type"],
        "training_years": base_payload["training_years"],
        "electricity_price_per_kwh": base_payload["electricity_price_per_kwh"],
        "currency": base_payload["currency"],
    }


def build_scenario_comparison_scenario(
    name: str,
    payload: Mapping[str, Any],
) -> ScenarioComparisonScenarioPayload:
    return {
        "name": name,
        "tilt": int(payload["tilt"]),
        "panel_area": float(payload["panel_area"]),
        "panel_efficiency": float(payload["panel_efficiency"]),
        "cleanliness": str(payload["cleanliness"]),
        "shading": str(payload["shading"]),
        "ac_capacity_kw": float(payload["ac_capacity_kw"]),
        "gamma": float(payload["gamma"]),
        "noct": float(payload["noct"]),
        "system_capex": float(payload["system_capex"]),
    }


def build_scenario_comparison_payload(
    base_payload: PVRequestPayload,
    scenario_requests: list[dict[str, Any]],
) -> ScenarioComparisonRequestPayload:
    scenarios = [
        build_scenario_comparison_scenario("Base System", base_payload),
        *[
            build_scenario_comparison_scenario(scenario["name"], scenario["payload"])
            for scenario in scenario_requests
        ],
    ]
    return {
        "context": build_scenario_comparison_context(base_payload),
        "scenarios": scenarios,
    }


def build_benchmark_payload(
    base_payload: PVRequestPayload,
    benchmark_years: int,
    evaluation_year: int,
) -> BenchmarkEvaluationPayload:
    return {
        "latitude": base_payload["latitude"],
        "longitude": base_payload["longitude"],
        "year": evaluation_year,
        "benchmark_years": benchmark_years,
        "tilt": base_payload["tilt"],
        "panel_area": base_payload["panel_area"],
        "panel_efficiency": base_payload["panel_efficiency"],
        "cleanliness": base_payload["cleanliness"],
        "shading": base_payload["shading"],
        "ac_capacity_kw": base_payload["ac_capacity_kw"],
        "gamma": base_payload["gamma"],
        "noct": base_payload["noct"],
        "training_years": base_payload["training_years"],
    }


def format_payback_years(payback_years: float | None) -> str:
    if payback_years is None or pd.isna(payback_years):
        return "Not viable"
    return f"{payback_years} years"
