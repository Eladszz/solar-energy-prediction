import math

from solar_ui.payloads import (
    build_benchmark_payload,
    build_demo_variant_requests,
    build_scenario_comparison_payload,
    format_payback_years,
)


BASE_PAYLOAD = {
    "latitude": 32.0853,
    "longitude": 34.7818,
    "year": 2026,
    "tilt": 30,
    "panel_area": 80.0,
    "panel_efficiency": 0.2,
    "cleanliness": "normal",
    "shading": "low",
    "ac_capacity_kw": 15.0,
    "gamma": 0.004,
    "noct": 45.0,
    "model_type": "ml",
    "electricity_price_per_kwh": 0.48,
    "currency": "ILS",
    "system_capex": 25000.0,
    "training_years": 3,
    "demo_mode": True,
    "demo_scenario_id": "tel_aviv_rooftop",
}


def test_build_demo_variant_requests_overrides_scenario_specific_fields():
    scenario = {
        "comparison_variants": [
            {
                "name": "Expanded Array",
                "panel_area": 120.0,
                "tilt": 20,
                "ac_capacity_kw": 18.0,
                "cleanliness": "clean",
                "shading": "none",
                "system_capex": 32000.0,
            }
        ]
    }

    variants = build_demo_variant_requests(BASE_PAYLOAD, scenario)

    assert variants == [
        {
            "name": "Expanded Array",
            "payload": {
                **BASE_PAYLOAD,
                "panel_area": 120.0,
                "tilt": 20,
                "ac_capacity_kw": 18.0,
                "cleanliness": "clean",
                "shading": "none",
                "system_capex": 32000.0,
            },
        }
    ]


def test_build_scenario_comparison_payload_uses_shared_context_and_base_case():
    scenario_requests = [
        {
            "name": "Larger Rooftop",
            "payload": {
                **BASE_PAYLOAD,
                "panel_area": 110.0,
                "system_capex": 31000.0,
            },
        }
    ]

    payload = build_scenario_comparison_payload(BASE_PAYLOAD, scenario_requests)

    assert payload["context"] == {
        "latitude": 32.0853,
        "longitude": 34.7818,
        "year": 2026,
        "model_type": "ml",
        "training_years": 3,
        "electricity_price_per_kwh": 0.48,
        "currency": "ILS",
        "demo_mode": True,
        "demo_scenario_id": "tel_aviv_rooftop",
    }
    assert [scenario["name"] for scenario in payload["scenarios"]] == [
        "Base System",
        "Larger Rooftop",
    ]
    assert payload["scenarios"][1]["system_capex"] == 31000.0


def test_build_benchmark_payload_reuses_baseline_system_configuration():
    payload = build_benchmark_payload(
        BASE_PAYLOAD,
        benchmark_years=4,
        evaluation_year=2025,
    )

    assert payload["year"] == 2025
    assert payload["benchmark_years"] == 4
    assert payload["tilt"] == BASE_PAYLOAD["tilt"]
    assert payload["panel_area"] == BASE_PAYLOAD["panel_area"]
    assert payload["training_years"] == BASE_PAYLOAD["training_years"]
    assert payload["demo_mode"] is True


def test_format_payback_years_handles_missing_and_numeric_values():
    assert format_payback_years(None) == "Not viable"
    assert format_payback_years(math.nan) == "Not viable"
    assert format_payback_years(7.4) == "7.4 years"
