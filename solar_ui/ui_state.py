from __future__ import annotations

from importlib import import_module
from typing import Any, Mapping

import pandas as pd
import streamlit as st  # type: ignore
from loguru import logger

try:
    from solar_ui.config import (
        DEMO_MODE_DEFAULT,
        get_default_demo_scenario_id,
    )
except ModuleNotFoundError:
    from config import (
        DEMO_MODE_DEFAULT,
        get_default_demo_scenario_id,
    )


FALLBACK_COUNTRIES = (
    "Australia",
    "Brazil",
    "Canada",
    "China",
    "France",
    "Germany",
    "India",
    "Israel",
    "Italy",
    "Japan",
    "Netherlands",
    "South Africa",
    "Spain",
    "United Arab Emirates",
    "United Kingdom",
    "United States",
)


def load_country_names() -> list[str]:
    try:
        countries_module = import_module("pycountry")
    except ModuleNotFoundError:
        logger.warning("pycountry is not installed; using fallback country list.")
        return sorted(FALLBACK_COUNTRIES)

    country_names = sorted(
        country.name
        for country in getattr(countries_module, "countries", ())
        if isinstance(getattr(country, "name", None), str)
    )
    return country_names or sorted(FALLBACK_COUNTRIES)


def initialize_session_state() -> None:
    defaults = {
        "lat": None,
        "lon": None,
        "address": None,
        "location_notice": None,
        "forecast_data": None,
        "daily_simulation": None,
        "comparison_result": None,
        "accuracy_result": None,
        "benchmark_result": None,
        "scenario_requests": [],
        "pending_panel_area": None,
        "last_drawing_id": None,
        "auto_run_forecast": False,
        "last_run_payload": None,
        "last_accuracy_payload": None,
        "last_benchmark_payload": None,
        "last_comparison_payload": None,
        "demo_mode": DEMO_MODE_DEFAULT,
        "demo_scenario_id": get_default_demo_scenario_id(),
        "last_applied_demo_scenario_id": None,
        "selected_scenario_index": 0,
        "editing_scenario_index": None,
        "scenario_form_name": "",
        "scenario_form_panel_area": 0.0,
        "scenario_form_tilt": 30,
        "scenario_form_ac_capacity": 0.0,
        "scenario_form_capex": 0.0,
        "scenario_form_cleanliness": "normal",
        "scenario_form_shading": "low",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_demo_scenario(scenario: Mapping[str, Any]) -> Mapping[str, Any]:
    defaults = scenario["system_defaults"]
    st.session_state.lat = float(scenario["latitude"])
    st.session_state.lon = float(scenario["longitude"])
    st.session_state.address = scenario["address"]
    st.session_state.location_notice = (
        f"Demo scenario loaded: {scenario['name']}. Geocoding and weather now use bundled fixtures."
    )
    st.session_state.country_select = scenario["country"]
    st.session_state.city_input = scenario["city"]
    st.session_state.street_input = scenario["street"]
    st.session_state.house_number_input = scenario["number"]
    st.session_state.panel_area = float(defaults["panel_area"])
    st.session_state.ac_capacity_kw_input = float(defaults["ac_capacity_kw"])
    st.session_state.forecast_year_input = int(defaults["year"])
    st.session_state.model_type_select = defaults["model_type"]
    st.session_state.training_years_slider = int(defaults["training_years"])
    st.session_state.tariff_input = float(defaults["electricity_price_per_kwh"])
    st.session_state.currency_select = defaults["currency"]
    st.session_state.system_capex_input = float(defaults["system_capex"])
    st.session_state.panel_efficiency_slider = float(defaults["panel_efficiency"])
    st.session_state.tilt_slider = int(defaults["tilt"])
    st.session_state.cleanliness_select = defaults["cleanliness"]
    st.session_state.shading_select = defaults["shading"]
    st.session_state.gamma_input = float(defaults["gamma"])
    st.session_state.noct_input = float(defaults["noct"])
    st.session_state.last_applied_demo_scenario_id = scenario["id"]
    return scenario


def seed_scenario_form(
    base_payload: Mapping[str, Any],
    *,
    name: str | None = None,
    payload: Mapping[str, Any] | None = None,
    editing_index: int | None = None,
) -> None:
    selected_payload = payload or base_payload
    st.session_state.scenario_form_name = name or f"Scenario {len(st.session_state.scenario_requests) + 1}"
    st.session_state.scenario_form_panel_area = float(selected_payload["panel_area"])
    st.session_state.scenario_form_tilt = int(selected_payload["tilt"])
    st.session_state.scenario_form_ac_capacity = float(selected_payload["ac_capacity_kw"])
    st.session_state.scenario_form_capex = float(selected_payload["system_capex"])
    st.session_state.scenario_form_cleanliness = str(selected_payload["cleanliness"])
    st.session_state.scenario_form_shading = str(selected_payload["shading"])
    st.session_state.editing_scenario_index = editing_index


def clear_scenario_editor(base_payload: Mapping[str, Any]) -> None:
    seed_scenario_form(base_payload, editing_index=None)


def upsert_scenario_request(
    scenario_requests: list[dict[str, Any]],
    *,
    name: str,
    payload: Mapping[str, Any],
    editing_index: int | None,
) -> list[dict[str, Any]]:
    updated_requests = list(scenario_requests)
    scenario_entry = {"name": name, "payload": dict(payload)}
    if editing_index is None:
        updated_requests.append(scenario_entry)
    else:
        updated_requests[editing_index] = scenario_entry
    return updated_requests


def remove_scenario_request(
    scenario_requests: list[dict[str, Any]],
    editing_index: int,
) -> list[dict[str, Any]]:
    updated_requests = list(scenario_requests)
    updated_requests.pop(editing_index)
    return updated_requests


def duplicate_scenario_request(
    scenario_requests: list[dict[str, Any]],
    editing_index: int,
) -> list[dict[str, Any]]:
    updated_requests = list(scenario_requests)
    selected = updated_requests[editing_index]
    duplicate_payload = dict(selected["payload"])
    updated_requests.append(
        {
            "name": f"{selected['name']} Copy",
            "payload": duplicate_payload,
        }
    )
    return updated_requests


def build_scenario_table(scenario_requests: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Scenario": scenario["name"],
                "Panel Area (m²)": scenario["payload"]["panel_area"],
                "Tilt (°)": scenario["payload"]["tilt"],
                "AC Capacity (kW)": scenario["payload"]["ac_capacity_kw"],
                "System CAPEX": scenario["payload"]["system_capex"],
                "Cleanliness": scenario["payload"]["cleanliness"],
                "Shading": scenario["payload"]["shading"],
            }
            for scenario in scenario_requests
        ]
    )
