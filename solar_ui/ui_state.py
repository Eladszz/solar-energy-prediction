from __future__ import annotations

from importlib import import_module
from typing import Any, Mapping

import pandas as pd
import streamlit as st  # type: ignore
from loguru import logger


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
