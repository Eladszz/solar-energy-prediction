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
    demo_mode: bool
    demo_scenario_id: str | None


class ScenarioComparisonContextPayload(TypedDict):
    latitude: float
    longitude: float
    year: int
    model_type: str
    training_years: int
    electricity_price_per_kwh: float
    currency: str
    demo_mode: bool
    demo_scenario_id: str | None


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
    demo_mode: bool
    demo_scenario_id: str | None


ApiPayload: TypeAlias = (
    PVRequestPayload
    | BenchmarkEvaluationPayload
    | ScenarioComparisonRequestPayload
    | dict[str, Any]
    | list[PVRequestPayload]
    | list[dict[str, Any]]
)


def build_demo_option_label(scenario: Mapping[str, Any]) -> str:
    return f"{scenario['name']} ({scenario['city']})"


def build_demo_variant_requests(
    base_payload: PVRequestPayload,
    scenario: Mapping[str, Any],
) -> list[dict[str, Any]]:
    variants = []
    for variant in scenario.get("comparison_variants", []):
        variant_payload = dict(base_payload)
        variant_payload.update(
            {
                "panel_area": float(variant["panel_area"]),
                "tilt": int(variant["tilt"]),
                "ac_capacity_kw": float(variant["ac_capacity_kw"]),
                "cleanliness": str(variant["cleanliness"]),
                "shading": str(variant["shading"]),
                "system_capex": float(
                    variant.get("system_capex", base_payload["system_capex"])
                ),
            }
        )
        variants.append({"name": str(variant["name"]), "payload": variant_payload})
    return variants


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
    demo_mode: bool,
    demo_scenario_id: str | None,
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
        "demo_mode": demo_mode,
        "demo_scenario_id": demo_scenario_id,
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
        "demo_mode": base_payload["demo_mode"],
        "demo_scenario_id": base_payload["demo_scenario_id"],
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
        "demo_mode": base_payload["demo_mode"],
        "demo_scenario_id": base_payload["demo_scenario_id"],
    }


def format_payback_years(payback_years: float | None) -> str:
    if payback_years is None or pd.isna(payback_years):
        return "Not viable"
    return f"{payback_years} years"
