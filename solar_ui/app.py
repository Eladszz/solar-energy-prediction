from __future__ import annotations

from datetime import date
import sys
from typing import Any, Mapping

import folium  # type: ignore
from folium.plugins import Draw  # type: ignore
from loguru import logger
from solar_backend.app.defaults import DEFAULT_SYSTEM_CAPEX
import streamlit as st  # type: ignore
from streamlit_folium import st_folium  # type: ignore

try:
    from solar_ui.api_client import api_post
    from solar_ui.config import (
        get_default_demo_scenario_id,
        get_demo_scenario_by_id,
        get_demo_scenarios,
    )
    from solar_ui.payloads import (
        BenchmarkEvaluationPayload,
        PVRequestPayload,
        build_benchmark_payload,
        build_common_payload,
        build_demo_option_label,
        build_demo_variant_requests,
        build_scenario_comparison_payload,
    )
    from solar_ui.ui_sections import (
        render_accuracy_tab,
        render_benchmark_tab,
        render_comparison_tab,
        render_daily_tab,
        render_last_benchmark_summary,
        render_last_run_summary,
        render_overview_tab,
        render_section_intro,
    )
    from solar_ui.ui_state import (
        apply_demo_scenario,
        build_scenario_table,
        clear_scenario_editor,
        duplicate_scenario_request,
        initialize_session_state,
        load_country_names,
        remove_scenario_request,
        seed_scenario_form,
        upsert_scenario_request,
    )
    from solar_ui.utils import (
        estimate_area_m2_from_bounds,
        geocode_address,
        reverse_geocode,
    )
except ModuleNotFoundError:
    from api_client import api_post
    from config import (
        get_default_demo_scenario_id,
        get_demo_scenario_by_id,
        get_demo_scenarios,
    )
    from payloads import (
        BenchmarkEvaluationPayload,
        PVRequestPayload,
        build_benchmark_payload,
        build_common_payload,
        build_demo_option_label,
        build_demo_variant_requests,
        build_scenario_comparison_payload,
    )
    from ui_sections import (
        render_accuracy_tab,
        render_benchmark_tab,
        render_comparison_tab,
        render_daily_tab,
        render_last_benchmark_summary,
        render_last_run_summary,
        render_overview_tab,
        render_section_intro,
    )
    from ui_state import (
        apply_demo_scenario,
        build_scenario_table,
        clear_scenario_editor,
        duplicate_scenario_request,
        initialize_session_state,
        load_country_names,
        remove_scenario_request,
        seed_scenario_form,
        upsert_scenario_request,
    )
    from utils import estimate_area_m2_from_bounds, geocode_address, reverse_geocode


logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    enqueue=True,
    backtrace=False,
    diagnose=False,
    colorize=True,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ),
)

st.set_page_config(page_title="Solar Energy Forecast", layout="wide")
st.title("Solar Energy Prediction System")
st.caption(
    "Demo-ready solar forecasting with physical and ML yearly forecasts, benchmark evaluation, "
    "backtest accuracy analysis, and scenario comparison."
)
st.info(
    "Recommended flow: locate a site, confirm the baseline system, run the forecast, then use "
    "comparison, backtest, and benchmark tabs to explore alternatives."
)


DEMO_SCENARIOS = get_demo_scenarios()
DEMO_SCENARIO_OPTIONS = {scenario["id"]: scenario for scenario in DEMO_SCENARIOS}


def payload_changed(
    current_payload: Mapping[str, Any] | None,
    previous_payload: Mapping[str, Any] | None,
) -> bool:
    if current_payload is None or previous_payload is None:
        return False
    return current_payload != previous_payload


def clear_analysis_results() -> None:
    st.session_state.forecast_data = None
    st.session_state.daily_simulation = None
    st.session_state.comparison_result = None
    st.session_state.accuracy_result = None
    st.session_state.benchmark_result = None
    st.session_state.last_run_payload = None
    st.session_state.last_accuracy_payload = None
    st.session_state.last_benchmark_payload = None
    st.session_state.last_comparison_payload = None


def clear_comparison_results() -> None:
    st.session_state.comparison_result = None
    st.session_state.last_comparison_payload = None


def render_location_map(
    *,
    demo_mode_active: bool,
    selected_demo_scenario_id: str | None,
) -> None:
    if st.session_state.lat is None or st.session_state.lon is None:
        st.info(
            "Resolve an address first to unlock the site map and optional roof-area selection."
        )
        return

    map_object = folium.Map(
        location=[st.session_state.lat, st.session_state.lon],
        zoom_start=18,
    )
    folium.Marker(
        [st.session_state.lat, st.session_state.lon],
        popup=st.session_state.address,
        icon=folium.Icon(icon="home"),
    ).add_to(map_object)
    if not demo_mode_active:
        Draw(
            draw_options={
                "polyline": False,
                "polygon": False,
                "circle": False,
                "circlemarker": False,
                "marker": False,
                "rectangle": True,
            },
            edit_options={"edit": True},
        ).add_to(map_object)
    map_data = st_folium(map_object, height=360, use_container_width=True)

    if demo_mode_active:
        st.caption(
            "Map editing is disabled in demo mode so the bundled scenario stays deterministic."
        )
        return

    if not map_data or not map_data.get("all_drawings"):
        st.caption(
            "Draw a roof rectangle to estimate usable panel area from the selected site."
        )
        return

    last_shape = map_data["all_drawings"][-1]
    drawing_id = last_shape.get("id") or hash(str(last_shape))
    if drawing_id == st.session_state.last_drawing_id:
        return

    st.session_state.last_drawing_id = drawing_id
    coordinates = last_shape["geometry"]["coordinates"][0]
    latitudes = [coordinate[1] for coordinate in coordinates]
    longitudes = [coordinate[0] for coordinate in coordinates]
    bounds = [[min(latitudes), min(longitudes)], [max(latitudes), max(longitudes)]]
    roof_area = estimate_area_m2_from_bounds(bounds)
    center_lat = sum(latitudes) / len(latitudes)
    center_lon = sum(longitudes) / len(longitudes)

    st.session_state.pending_panel_area = round(roof_area, 1)
    st.session_state.lat = center_lat
    st.session_state.lon = center_lon

    reverse_lookup = reverse_geocode(
        center_lat,
        center_lon,
        demo_mode=demo_mode_active,
        demo_scenario_id=selected_demo_scenario_id,
    )
    if reverse_lookup.address:
        st.session_state.address = reverse_lookup.address
        st.session_state.location_notice = None
    else:
        st.session_state.address = f"{center_lat:.5f}, {center_lon:.5f}"
        st.session_state.location_notice = reverse_lookup.error_message

    st.session_state.auto_run_forecast = True
    st.success(
        f"Roof area detected: {roof_area:.1f} m². Location and panel area were updated."
    )
    st.rerun()


def build_scenario_preview_payload(base_payload: PVRequestPayload) -> dict[str, Any]:
    scenario_payload = dict(base_payload)
    scenario_payload["panel_area"] = float(st.session_state.scenario_form_panel_area)
    scenario_payload["tilt"] = int(st.session_state.scenario_form_tilt)
    scenario_payload["ac_capacity_kw"] = float(
        st.session_state.scenario_form_ac_capacity
    )
    scenario_payload["system_capex"] = float(st.session_state.scenario_form_capex)
    scenario_payload["cleanliness"] = str(st.session_state.scenario_form_cleanliness)
    scenario_payload["shading"] = str(st.session_state.scenario_form_shading)
    return scenario_payload


def render_scenario_editor(base_payload: PVRequestPayload) -> None:
    render_section_intro(
        "Scenario Comparison",
        "Create alternative system designs against the current baseline. Scenarios inherit the "
        "baseline location, year, model choice, tariff, currency, and demo settings.",
        "Use the editor below to tune one scenario at a time, then run the comparison when the "
        "saved list looks right.",
    )

    if st.session_state.editing_scenario_index is not None and (
        st.session_state.editing_scenario_index
        >= len(st.session_state.scenario_requests)
    ):
        clear_scenario_editor(base_payload)

    if (
        not st.session_state.scenario_form_name
        or st.session_state.scenario_form_panel_area <= 0
        or st.session_state.scenario_form_ac_capacity <= 0
    ):
        clear_scenario_editor(base_payload)

    base_columns = st.columns(4)
    base_columns[0].metric("Baseline Area", f"{base_payload['panel_area']} m²")
    base_columns[1].metric("Baseline Tilt", f"{base_payload['tilt']}°")
    base_columns[2].metric(
        "Baseline AC Capacity", f"{base_payload['ac_capacity_kw']} kW"
    )
    base_columns[3].metric(
        "Baseline CAPEX", f"{base_payload['system_capex']} {base_payload['currency']}"
    )

    if st.session_state.scenario_requests:
        selected_index = st.session_state.selected_scenario_index
        if selected_index >= len(st.session_state.scenario_requests):
            st.session_state.selected_scenario_index = (
                len(st.session_state.scenario_requests) - 1
            )

        manager_columns = st.columns([2.4, 1, 1, 1])
        selected_index = manager_columns[0].selectbox(
            "Saved Scenario",
            options=list(range(len(st.session_state.scenario_requests))),
            format_func=lambda index: st.session_state.scenario_requests[index]["name"],
            key="selected_scenario_index",
        )
        if manager_columns[1].button("Edit", use_container_width=True):
            selected = st.session_state.scenario_requests[selected_index]
            seed_scenario_form(
                base_payload,
                name=selected["name"],
                payload=selected["payload"],
                editing_index=selected_index,
            )
        if manager_columns[2].button("Duplicate", use_container_width=True):
            st.session_state.scenario_requests = duplicate_scenario_request(
                st.session_state.scenario_requests,
                selected_index,
            )
            st.session_state.selected_scenario_index = (
                len(st.session_state.scenario_requests) - 1
            )
            clear_comparison_results()
        if manager_columns[3].button("Remove", use_container_width=True):
            st.session_state.scenario_requests = remove_scenario_request(
                st.session_state.scenario_requests,
                selected_index,
            )
            st.session_state.selected_scenario_index = max(
                0,
                min(selected_index, len(st.session_state.scenario_requests) - 1),
            )
            clear_comparison_results()
            if st.session_state.editing_scenario_index == selected_index:
                clear_scenario_editor(base_payload)

    utility_columns = st.columns([1, 1, 1])
    if utility_columns[0].button("New From Baseline", use_container_width=True):
        clear_scenario_editor(base_payload)
    if utility_columns[1].button("Clear All Scenarios", use_container_width=True):
        st.session_state.scenario_requests = []
        st.session_state.selected_scenario_index = 0
        clear_scenario_editor(base_payload)
        clear_comparison_results()
    if utility_columns[2].button("Reset Form", use_container_width=True):
        clear_scenario_editor(base_payload)

    st.markdown(
        f"**{'Edit scenario' if st.session_state.editing_scenario_index is not None else 'Create scenario'}**"
    )
    name = st.text_input("Scenario Name", key="scenario_form_name")

    config_columns = st.columns(4)
    panel_area = config_columns[0].number_input(
        "Panel Area (m²)",
        min_value=0.1,
        value=float(st.session_state.scenario_form_panel_area),
        key="scenario_form_panel_area",
    )
    tilt = config_columns[1].slider(
        "Tilt (°)",
        min_value=0,
        max_value=60,
        value=int(st.session_state.scenario_form_tilt),
        key="scenario_form_tilt",
    )
    ac_capacity = config_columns[2].number_input(
        "AC Capacity (kW)",
        min_value=0.1,
        value=float(st.session_state.scenario_form_ac_capacity),
        key="scenario_form_ac_capacity",
    )
    capex = config_columns[3].number_input(
        "System CAPEX",
        min_value=0.0,
        value=float(st.session_state.scenario_form_capex),
        step=500.0,
        key="scenario_form_capex",
    )

    quality_columns = st.columns(2)
    cleanliness = quality_columns[0].selectbox(
        "Panel Cleanliness",
        options=["clean", "normal", "dusty"],
        index=["clean", "normal", "dusty"].index(
            st.session_state.scenario_form_cleanliness
        ),
        key="scenario_form_cleanliness",
    )
    shading = quality_columns[1].selectbox(
        "Shading Level",
        options=["none", "low", "medium", "high"],
        index=["none", "low", "medium", "high"].index(
            st.session_state.scenario_form_shading
        ),
        key="scenario_form_shading",
    )

    preview_columns = st.columns(4)
    preview_columns[0].metric(
        "Area Delta",
        f"{panel_area:.1f} m²",
        f"{panel_area - base_payload['panel_area']:+.1f} m²",
    )
    preview_columns[1].metric(
        "Tilt Delta",
        f"{tilt}°",
        f"{tilt - base_payload['tilt']:+d}°",
    )
    preview_columns[2].metric(
        "AC Delta",
        f"{ac_capacity:.1f} kW",
        f"{ac_capacity - base_payload['ac_capacity_kw']:+.1f} kW",
    )
    preview_columns[3].metric(
        "CAPEX Delta",
        f"{capex:.0f} {base_payload['currency']}",
        f"{capex - base_payload['system_capex']:+.0f} {base_payload['currency']}",
    )

    button_label = (
        "Update Scenario"
        if st.session_state.editing_scenario_index is not None
        else "Add Scenario"
    )
    if st.button(button_label, type="primary"):
        if not name.strip():
            st.error("Scenario name is required.")
        else:
            scenario_payload = build_scenario_preview_payload(base_payload)
            editing_index = st.session_state.editing_scenario_index
            st.session_state.scenario_requests = upsert_scenario_request(
                st.session_state.scenario_requests,
                name=name.strip(),
                payload=scenario_payload,
                editing_index=editing_index,
            )
            saved_index = (
                editing_index
                if editing_index is not None
                else len(st.session_state.scenario_requests) - 1
            )
            st.session_state.selected_scenario_index = saved_index
            seed_scenario_form(
                base_payload,
                name=name.strip(),
                payload=scenario_payload,
                editing_index=saved_index,
            )
            clear_comparison_results()
            st.success(f"Scenario '{name.strip()}' saved.")

    st.caption(
        "Scenario-specific fields are limited to system design assumptions. Location, forecast year, "
        "tariff, currency, model selection, and demo settings remain shared baseline context."
    )


initialize_session_state()

countries = load_country_names()
default_country = "Israel" if "Israel" in countries else countries[0]
current_year = date.today().year
last_complete_year = current_year - 1

if "country_select" not in st.session_state:
    st.session_state.country_select = default_country
if "city_input" not in st.session_state:
    st.session_state.city_input = "Tel Aviv"
if "street_input" not in st.session_state:
    st.session_state.street_input = "Dizengoff"
if "house_number_input" not in st.session_state:
    st.session_state.house_number_input = "100"

demo_scenario_reset_requested = False
selected_demo_scenario: Mapping[str, Any] | None = None

st.sidebar.header("Demo Controls")
demo_mode_active = st.sidebar.checkbox(
    "Enable Demo Mode",
    key="demo_mode",
    help="Uses bundled geocoding and deterministic weather fixtures instead of live third-party services.",
)
selected_demo_scenario_id = st.session_state.demo_scenario_id
if demo_mode_active:
    if selected_demo_scenario_id not in DEMO_SCENARIO_OPTIONS:
        selected_demo_scenario_id = get_default_demo_scenario_id()
        st.session_state.demo_scenario_id = selected_demo_scenario_id

    selected_demo_scenario_id = st.sidebar.selectbox(
        "Demo Scenario",
        options=list(DEMO_SCENARIO_OPTIONS),
        format_func=lambda scenario_id: build_demo_option_label(
            DEMO_SCENARIO_OPTIONS[scenario_id]
        ),
        key="demo_scenario_id",
    )
    demo_scenario_reset_requested = (
        st.session_state.last_applied_demo_scenario_id != selected_demo_scenario_id
    )
    selected_demo_scenario = get_demo_scenario_by_id(selected_demo_scenario_id)
    if (
        demo_scenario_reset_requested
        or st.session_state.lat is None
        or st.session_state.lon is None
    ):
        selected_demo_scenario = apply_demo_scenario(selected_demo_scenario)
        st.session_state.scenario_requests = []
        st.session_state.selected_scenario_index = 0
        clear_analysis_results()
    st.sidebar.caption(selected_demo_scenario["description"])
else:
    st.session_state.demo_scenario_id = None
    st.session_state.last_applied_demo_scenario_id = None

if demo_mode_active and selected_demo_scenario is not None:
    st.warning(
        "Demo mode is active. Geocoding, forecast weather, scenario comparison, benchmark, and "
        f"backtest flows are using the bundled '{selected_demo_scenario['name']}' dataset."
    )

st.sidebar.header("Location")
country_value = st.session_state.country_select
if country_value not in countries:
    countries = sorted(set(countries + [country_value]))
country = st.sidebar.selectbox(
    "Country",
    countries,
    index=countries.index(country_value),
    key="country_select",
)
city = st.sidebar.text_input(
    "City", value=st.session_state.get("city_input", "Tel Aviv"), key="city_input"
)
street = st.sidebar.text_input(
    "Street",
    value=st.session_state.get("street_input", "Dizengoff"),
    key="street_input",
)
number = st.sidebar.text_input(
    "Number",
    value=st.session_state.get("house_number_input", "100"),
    key="house_number_input",
)

address = f"{street} {number}, {city}, {country}".strip()
if st.sidebar.button("Locate Address", type="primary"):
    location_lookup = geocode_address(
        address,
        demo_mode=demo_mode_active,
        demo_scenario_id=selected_demo_scenario_id,
    )
    if location_lookup.is_success:
        st.session_state.lat = location_lookup.latitude
        st.session_state.lon = location_lookup.longitude
        st.session_state.address = location_lookup.address or address
        st.session_state.location_notice = (
            "Using bundled geocoding for demo mode." if demo_mode_active else None
        )
        st.success(
            f"Location resolved to {st.session_state.lat:.4f}, {st.session_state.lon:.4f}"
        )
    else:
        st.session_state.location_notice = location_lookup.error_message
        st.error(location_lookup.error_message or "Address lookup failed.")

st.sidebar.markdown("### Detected Address")
if st.session_state.address:
    st.sidebar.info(st.session_state.address)
else:
    st.sidebar.caption("No address selected yet.")

if st.session_state.location_notice:
    st.sidebar.warning(st.session_state.location_notice)

st.sidebar.header("System Parameters")
if st.session_state.pending_panel_area is not None:
    st.session_state.panel_area = st.session_state.pending_panel_area
    st.session_state.pending_panel_area = None

forecast_year = st.sidebar.number_input(
    "Forecast Year",
    min_value=2020,
    max_value=current_year + 2,
    value=int(st.session_state.get("forecast_year_input", current_year)),
    step=1,
    key="forecast_year_input",
)
panel_area = st.sidebar.number_input(
    "Panel Area (m²)",
    min_value=0.1,
    value=st.session_state.get("panel_area", 80.0),
    key="panel_area",
)
ac_capacity_kw = st.sidebar.number_input(
    "Inverter AC Capacity (kW)",
    min_value=0.1,
    value=st.session_state.get("ac_capacity_kw_input", 15.0),
    key="ac_capacity_kw_input",
)
model_type = st.sidebar.selectbox(
    "Forecast Model",
    options=["physical", "ml"],
    format_func=lambda value: (
        "Physical baseline" if value == "physical" else "ML baseline"
    ),
    index=["physical", "ml"].index(
        st.session_state.get("model_type_select", "physical")
    ),
    key="model_type_select",
)
training_years = st.sidebar.slider(
    "ML Training Window (years)",
    min_value=2,
    max_value=5,
    value=int(st.session_state.get("training_years_slider", 3)),
    disabled=model_type != "ml",
    key="training_years_slider",
)
electricity_price_per_kwh = st.sidebar.number_input(
    "Electricity Price / Feed-in Tariff",
    min_value=0.0,
    value=float(st.session_state.get("tariff_input", 0.48)),
    step=0.01,
    format="%.2f",
    key="tariff_input",
)
currency_options = ["ILS", "USD", "EUR"]
currency = st.sidebar.selectbox(
    "Currency",
    options=currency_options,
    index=currency_options.index(st.session_state.get("currency_select", "ILS")),
    key="currency_select",
)
current_system_capex = float(st.session_state.get("system_capex_input", DEFAULT_SYSTEM_CAPEX))

system_capex = st.sidebar.number_input(
    "System CAPEX",
    min_value=0.0,
    value=DEFAULT_SYSTEM_CAPEX if current_system_capex <= 0 else current_system_capex,
    step=500.0,
    key="system_capex_input",
)

with st.sidebar.expander("Advanced Settings", expanded=False):
    panel_efficiency = st.slider(
        "Panel Efficiency",
        0.10,
        0.30,
        float(st.session_state.get("panel_efficiency_slider", 0.20)),
        key="panel_efficiency_slider",
    )
    tilt = st.slider(
        "Tilt Angle (°)",
        0,
        60,
        int(st.session_state.get("tilt_slider", 30)),
        key="tilt_slider",
    )
    cleanliness = st.selectbox(
        "Panel Cleanliness",
        options=["clean", "normal", "dusty"],
        index=["clean", "normal", "dusty"].index(
            st.session_state.get("cleanliness_select", "normal")
        ),
        key="cleanliness_select",
    )
    shading = st.selectbox(
        "Shading Level",
        options=["none", "low", "medium", "high"],
        index=["none", "low", "medium", "high"].index(
            st.session_state.get("shading_select", "low")
        ),
        key="shading_select",
    )
    gamma = st.number_input(
        "Temperature Coefficient (gamma)",
        min_value=0.002,
        max_value=0.006,
        value=float(st.session_state.get("gamma_input", 0.004)),
        step=0.0001,
        format="%.4f",
        key="gamma_input",
    )
    noct = st.number_input(
        "NOCT (°C)",
        min_value=35.0,
        max_value=60.0,
        value=float(st.session_state.get("noct_input", 45.0)),
        step=1.0,
        key="noct_input",
    )

run_forecast = st.sidebar.button(
    "Run Baseline Forecast",
    type="primary",
    disabled=st.session_state.lat is None or st.session_state.lon is None,
    help="Runs the yearly baseline forecast and the daily simulation for the current site and system.",
)

render_location_map(
    demo_mode_active=demo_mode_active,
    selected_demo_scenario_id=selected_demo_scenario_id,
)

base_payload: PVRequestPayload | None = None
if st.session_state.lat is not None and st.session_state.lon is not None:
    base_payload = build_common_payload(
        latitude=float(st.session_state.lat),
        longitude=float(st.session_state.lon),
        year=int(forecast_year),
        tilt=int(tilt),
        panel_area=float(panel_area),
        panel_efficiency=float(panel_efficiency),
        cleanliness=cleanliness,
        shading=shading,
        ac_capacity_kw=float(ac_capacity_kw),
        gamma=float(gamma),
        noct=float(noct),
        model_type=model_type,
        electricity_price_per_kwh=float(electricity_price_per_kwh),
        currency=currency,
        system_capex=float(system_capex),
        training_years=int(training_years),
        demo_mode=demo_mode_active,
        demo_scenario_id=selected_demo_scenario_id if demo_mode_active else None,
    )

if base_payload is not None and demo_scenario_reset_requested:
    clear_scenario_editor(base_payload)

if run_forecast or st.session_state.auto_run_forecast:
    st.session_state.auto_run_forecast = False
    if base_payload is None:
        st.error("Select a valid location before running the forecast.")
    elif base_payload["panel_area"] <= 0:
        st.error("Panel area must be greater than zero.")
    else:
        with st.spinner("Running baseline yearly forecast and daily simulation..."):
            forecast_response = api_post("/forecast/yearly", base_payload)
            simulation_response = api_post("/simulate", base_payload)
        if forecast_response is not None:
            st.session_state.forecast_data = forecast_response
        if simulation_response is not None:
            st.session_state.daily_simulation = simulation_response
        if forecast_response is not None or simulation_response is not None:
            st.session_state.last_run_payload = dict(base_payload)
            st.session_state.last_accuracy_payload = None
            st.session_state.last_benchmark_payload = None
            st.session_state.last_comparison_payload = None
            st.session_state.accuracy_result = None
            st.session_state.benchmark_result = None
            st.session_state.comparison_result = None

tab_overview, tab_daily, tab_accuracy, tab_benchmark, tab_scenarios = st.tabs(
    [
        "Overview",
        "Daily Simulation",
        "Accuracy Backtest",
        "Benchmark Study",
        "Scenario Comparison",
    ]
)

with tab_overview:
    render_section_intro(
        "Baseline Forecast",
        "Start here for the main yearly forecast and finance summary of the selected site and system.",
        "Re-run the baseline forecast whenever the location or system assumptions change.",
    )
    if st.session_state.forecast_data is None:
        st.info(
            "Run the baseline forecast to see yearly energy, finance, and model diagnostics."
        )
    else:
        if payload_changed(base_payload, st.session_state.last_run_payload):
            st.warning(
                "Inputs changed after the last forecast run. Refresh the baseline forecast."
            )
            render_last_run_summary(st.session_state.last_run_payload)
        render_overview_tab(st.session_state.forecast_data)

with tab_daily:
    render_section_intro(
        "Daily Simulation",
        "Inspect the expected hourly production profile for the current baseline system.",
        "This uses the same assumptions as the last baseline forecast run.",
    )
    if st.session_state.daily_simulation is None:
        st.info(
            "Run the baseline forecast to generate the daily production simulation."
        )
    else:
        if payload_changed(base_payload, st.session_state.last_run_payload):
            st.warning(
                "Inputs changed after the last forecast run. Refresh the daily simulation."
            )
            render_last_run_summary(st.session_state.last_run_payload)
        render_daily_tab(st.session_state.daily_simulation)

with tab_accuracy:
    evaluation_year = min(int(forecast_year), last_complete_year)
    render_section_intro(
        "Accuracy Backtest",
        "Compare the selected forecast configuration against archived weather for a completed year.",
        (
            "Demo mode keeps this deterministic. Live mode uses the latest archived weather that is "
            f"fully available through {last_complete_year}."
        ),
    )
    if forecast_year > last_complete_year and not demo_mode_active:
        st.info(
            f"Archived actual weather is only complete through {last_complete_year}, so the backtest "
            f"uses {evaluation_year}."
        )

    accuracy_payload: PVRequestPayload | None = None
    if base_payload is not None:
        accuracy_payload = dict(base_payload)
        accuracy_payload["year"] = evaluation_year

    if base_payload is None:
        st.info("Select a location and system configuration first.")
    else:
        if st.button("Run Accuracy Backtest", type="primary"):
            with st.spinner("Evaluating baseline accuracy against archived weather..."):
                accuracy_response = api_post("/evaluation/accuracy", accuracy_payload)
            if accuracy_response is not None:
                st.session_state.accuracy_result = accuracy_response
                st.session_state.last_accuracy_payload = dict(accuracy_payload)
                st.success("Accuracy backtest completed.")

        if st.session_state.accuracy_result is None:
            st.info("Run the backtest to compare predicted and archived yearly output.")
        else:
            if payload_changed(
                accuracy_payload, st.session_state.last_accuracy_payload
            ):
                st.warning(
                    "Inputs changed after the last backtest run. Re-run the backtest to refresh the evaluation."
                )
                if st.session_state.last_accuracy_payload is not None:
                    render_last_run_summary(st.session_state.last_accuracy_payload)
            render_accuracy_tab(st.session_state.accuracy_result)

with tab_benchmark:
    evaluation_year = min(int(forecast_year), last_complete_year)
    render_section_intro(
        "Benchmark Study",
        "Compare physical, ML, and naive baselines across multiple historical years.",
        "This is useful for reviewer-facing evidence that the project is evaluating multiple forecast approaches.",
    )
    benchmark_years = st.slider(
        "Benchmark Window (years)",
        min_value=1,
        max_value=5,
        value=3,
        help="Evaluates physical, ML, and naive baselines over completed historical years.",
    )

    benchmark_payload: BenchmarkEvaluationPayload | None = None
    if base_payload is not None:
        benchmark_payload = build_benchmark_payload(
            base_payload=base_payload,
            benchmark_years=benchmark_years,
            evaluation_year=evaluation_year,
        )

    if base_payload is None:
        st.info("Select a location and system configuration first.")
    else:
        if st.button("Run Benchmark Study", type="primary"):
            with st.spinner(
                "Evaluating physical, ML, and naive benchmark baselines..."
            ):
                benchmark_response = api_post(
                    "/evaluation/benchmark", benchmark_payload
                )
            if benchmark_response is not None:
                st.session_state.benchmark_result = benchmark_response
                st.session_state.last_benchmark_payload = dict(benchmark_payload)
                st.success("Benchmark study completed.")

        if st.session_state.benchmark_result is None:
            st.info(
                "Run the benchmark to compare the physical, ML, and naive approaches."
            )
        else:
            if payload_changed(
                benchmark_payload, st.session_state.last_benchmark_payload
            ):
                st.warning(
                    "Inputs changed after the last benchmark run. Re-run the study to refresh the comparison."
                )
                render_last_benchmark_summary(st.session_state.last_benchmark_payload)
            render_benchmark_tab(st.session_state.benchmark_result)

with tab_scenarios:
    if base_payload is None or st.session_state.forecast_data is None:
        render_section_intro(
            "Scenario Comparison",
            "Compare alternative system designs against the current baseline forecast.",
            "Run the baseline forecast first so comparison starts from a clear shared context.",
        )
        st.info("Run the baseline forecast first to unlock scenario comparison.")
    else:
        render_scenario_editor(base_payload)

        if demo_mode_active and selected_demo_scenario is not None:
            if st.button("Load Demo Variants", use_container_width=True):
                variants = build_demo_variant_requests(
                    base_payload, selected_demo_scenario
                )
                if variants:
                    st.session_state.scenario_requests = variants
                    st.session_state.selected_scenario_index = 0
                    clear_scenario_editor(base_payload)
                    clear_comparison_results()
                    st.success(
                        "Loaded the bundled comparison variants for this demo scenario."
                    )
                else:
                    st.warning(
                        "This demo scenario does not define bundled comparison variants."
                    )

        if st.session_state.scenario_requests:
            st.markdown("**Saved scenarios**")
            st.dataframe(
                build_scenario_table(st.session_state.scenario_requests),
                width="stretch",
                hide_index=True,
            )
        else:
            st.info(
                "No alternative scenarios yet. Add one above or load the bundled demo variants."
            )

        comparison_payload = (
            build_scenario_comparison_payload(
                base_payload,
                st.session_state.scenario_requests,
            )
            if st.session_state.scenario_requests
            else None
        )

        compare_disabled = comparison_payload is None
        if st.button(
            "Run Scenario Comparison", type="primary", disabled=compare_disabled
        ):
            with st.spinner("Comparing yearly scenarios..."):
                comparison_response = api_post("/scenarios/compare", comparison_payload)
            if comparison_response is not None:
                st.session_state.comparison_result = comparison_response
                st.session_state.last_comparison_payload = dict(comparison_payload)
                st.success("Scenario comparison completed.")

        if st.session_state.comparison_result is None:
            st.info(
                "Save at least one scenario, then run the comparison to see energy and financial tradeoffs."
            )
        else:
            if payload_changed(
                comparison_payload, st.session_state.last_comparison_payload
            ):
                st.warning(
                    "Scenario inputs changed after the last comparison run. Re-run the comparison to refresh the results."
                )
            render_comparison_tab(st.session_state.comparison_result)
