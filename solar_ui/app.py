from __future__ import annotations

from datetime import date
from importlib import import_module
from inspect import isawaitable
import sys
from typing import TYPE_CHECKING, Any, Mapping, TypeAlias, TypedDict, cast

import folium  # type: ignore
from folium.plugins import Draw  # type: ignore
from geopy.geocoders import Nominatim  # type: ignore
from loguru import logger
import pandas as pd
import plotly.express as px
import requests
import streamlit as st  # type: ignore
from streamlit_folium import st_folium  # type: ignore

from utils import estimate_area_m2_from_bounds, reverse_geocode

if TYPE_CHECKING:
    from geopy.location import Location


BACKEND_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT_SECONDS = 90
MONTH_NAMES = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

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
    training_years: int


ApiPayload: TypeAlias = (
    PVRequestPayload
    | dict[str, Any]
    | list[PVRequestPayload]
    | list[dict[str, Any]]
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


def geocode_address(address: str) -> Location | None:
    geolocator = Nominatim(user_agent="solar_energy_prediction_alpha")
    location_result = geolocator.geocode(address)
    if isawaitable(location_result):
        logger.error("Unexpected awaitable geocode result for address lookup.")
        return None
    return cast("Location | None", location_result)

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
    "Alpha demo with physical and ML yearly forecasting, tariff-based value estimation, "
    "scenario comparison, and backtest accuracy analysis."
)


def initialize_session_state() -> None:
    defaults = {
        "lat": None,
        "lon": None,
        "address": None,
        "forecast_data": None,
        "daily_simulation": None,
        "comparison_result": None,
        "accuracy_result": None,
        "scenario_requests": [],
        "pending_panel_area": None,
        "last_drawing_id": None,
        "auto_run_forecast": False,
        "last_run_payload": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def parse_api_error(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    return payload.get("detail") or response.text or "Unknown backend error"


def api_post(path: str, payload: ApiPayload) -> dict[str, Any] | None:
    try:
        response = requests.post(
            f"{BACKEND_URL}{path}",
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        logger.error("Frontend request to {} failed: {}", path, exc)
        st.error(f"Request to backend failed: {exc}")
        return None

    if response.status_code != 200:
        error_message = parse_api_error(response)
        logger.error(
            "Backend request {} returned status {}: {}",
            path,
            response.status_code,
            error_message,
        )
        st.error(error_message)
        return None

    try:
        return response.json()
    except ValueError:
        logger.error("Backend response for {} was not valid JSON.", path)
        st.error("Backend response was not valid JSON.")
        return None


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
        "training_years": training_years,
    }


def render_summary_cards(forecast_data: dict) -> None:
    assumptions = forecast_data["financial_assumptions"]
    value_label = f"{forecast_data['yearly_estimated_value']} {assumptions['currency']}"

    metric_columns = st.columns(4)
    metric_columns[0].metric("Yearly Energy", f"{forecast_data['yearly_kwh']} kWh")
    metric_columns[1].metric("Yearly Value", value_label)
    metric_columns[2].metric(
        "Specific Yield",
        f"{forecast_data['specific_yield_kwh_per_kwp']} kWh/kWp",
    )
    metric_columns[3].metric(
        "Average Daily Energy",
        f"{forecast_data['avg_daily_kwh']} kWh",
    )

    info_columns = st.columns(4)
    info_columns[0].metric("Forecast Year", forecast_data["forecast_year"])
    info_columns[1].metric("Model Used", forecast_data["model_type_used"].upper())
    reference_year = forecast_data.get("weather_reference_year")
    if reference_year is None:
        reference_value = "ML profile"
    else:
        reference_value = str(reference_year)
    info_columns[2].metric("Weather Basis", reference_value)
    info_columns[3].metric(
        "Tariff Assumption",
        f"{assumptions['electricity_price_per_kwh']} {assumptions['currency']}/kWh",
    )


def render_metadata_table(rows: list[dict]) -> None:
    metadata_df = pd.DataFrame(rows)
    for column in metadata_df.columns:
        metadata_df[column] = metadata_df[column].astype(str)
    st.dataframe(metadata_df, width="stretch", hide_index=True)


def render_overview_tab(forecast_data: dict) -> None:
    render_summary_cards(forecast_data)

    if forecast_data.get("fallback_reason"):
        st.warning(forecast_data["fallback_reason"])

    monthly_df = pd.DataFrame(
        {
            "Month": MONTH_NAMES,
            "Energy (kWh)": forecast_data["monthly_kwh"],
            "Estimated Value": forecast_data["monthly_estimated_value"],
        }
    )

    chart_columns = st.columns(2)
    with chart_columns[0]:
        energy_chart = px.bar(
            monthly_df,
            x="Month",
            y="Energy (kWh)",
            title="Monthly Energy Forecast",
            color="Energy (kWh)",
            color_continuous_scale="YlOrBr",
        )
        energy_chart.update_layout(coloraxis_showscale=False)
        st.plotly_chart(energy_chart, width="stretch")

    with chart_columns[1]:
        value_chart = px.line(
            monthly_df,
            x="Month",
            y="Estimated Value",
            markers=True,
            title="Monthly Estimated Financial Value",
        )
        value_chart.update_layout(hovermode="x unified")
        st.plotly_chart(value_chart, width="stretch")

    with st.expander("Forecast Metadata and Assumptions", expanded=False):
        metadata_rows = [
            {
                "Field": "Requested model",
                "Value": forecast_data["model_type_requested"],
            },
            {
                "Field": "Model used",
                "Value": forecast_data["model_type_used"],
            },
            {
                "Field": "Forecast year",
                "Value": forecast_data["forecast_year"],
            },
            {
                "Field": "Archived weather reference year",
                "Value": forecast_data.get("weather_reference_year") or "Not used",
            },
            {
                "Field": "ML training years",
                "Value": ", ".join(map(str, forecast_data.get("training_years_used", [])))
                or "Not used",
            },
            {
                "Field": "Tariff assumption",
                "Value": (
                    f"{forecast_data['financial_assumptions']['electricity_price_per_kwh']} "
                    f"{forecast_data['financial_assumptions']['currency']}/kWh"
                ),
            },
        ]
        render_metadata_table(metadata_rows)

        if forecast_data.get("ml_metadata"):
            st.markdown("**ML training diagnostics**")
            st.json(forecast_data["ml_metadata"])


def render_daily_tab(daily_data: dict) -> None:
    assumptions = daily_data["financial_assumptions"]
    metric_columns = st.columns(4)
    metric_columns[0].metric("Daily Energy", f"{daily_data['daily_kwh']} kWh")
    metric_columns[1].metric(
        "Estimated Daily Value",
        f"{daily_data['estimated_daily_value']} {assumptions['currency']}",
    )
    metric_columns[2].metric("Average Power", f"{daily_data['avg_kw']} kW")
    metric_columns[3].metric("System Loss Factor", daily_data["system_loss_factor"])

    if daily_data.get("hourly_time"):
        time_labels = [
            timestamp.split("T")[1][:5] if "T" in timestamp else timestamp
            for timestamp in daily_data["hourly_time"]
        ]
    else:
        time_labels = [f"{hour:02d}:00" for hour in range(len(daily_data["hourly_ac_kw"]))]

    daily_df = pd.DataFrame(
        {
            "Time": time_labels,
            "AC Power (kW)": daily_data["hourly_ac_kw"],
        }
    )
    power_chart = px.line(
        daily_df,
        x="Time",
        y="AC Power (kW)",
        title=f"Hourly Production ({daily_data.get('timezone', 'UTC')})",
        markers=True,
    )
    power_chart.update_layout(hovermode="x unified")
    st.plotly_chart(power_chart, width="stretch")

    with st.expander("Daily Simulation Details", expanded=False):
        st.dataframe(daily_df, width="stretch", hide_index=True)


def payload_changed(
    current_payload: Mapping[str, Any] | None,
    previous_payload: Mapping[str, Any] | None,
) -> bool:
    if current_payload is None or previous_payload is None:
        return False
    return current_payload != previous_payload


def render_last_run_summary(last_run_payload: Mapping[str, Any]) -> None:
    run_rows = [
        {"Parameter": "Panel Area (m²)", "Value": str(last_run_payload["panel_area"])},
        {
            "Parameter": "Inverter AC Capacity (kW)",
            "Value": str(last_run_payload["ac_capacity_kw"]),
        },
        {"Parameter": "Panel Efficiency", "Value": str(last_run_payload["panel_efficiency"])},
        {"Parameter": "Tilt (°)", "Value": str(last_run_payload["tilt"])},
        {"Parameter": "Model Type", "Value": str(last_run_payload["model_type"])},
    ]
    st.caption("Displayed results are based on the last executed forecast payload.")
    st.dataframe(pd.DataFrame(run_rows), width="stretch", hide_index=True)


def render_accuracy_tab(accuracy_data: dict) -> None:
    assumptions = accuracy_data["financial_assumptions"]
    delta_percent = 0.0
    if accuracy_data["actual_yearly_kwh"] != 0:
        delta_percent = round(
            100
            * (
                accuracy_data["predicted_yearly_kwh"]
                - accuracy_data["actual_yearly_kwh"]
            )
            / accuracy_data["actual_yearly_kwh"],
            2,
        )

    metrics = st.columns(4)
    metrics[0].metric("Monthly MAPE", f"{accuracy_data['mape_percent']}%")
    metrics[1].metric("Yearly MAPE", f"{accuracy_data['yearly_mape_percent']}%")
    metrics[2].metric("Quality", accuracy_data["quality"])
    metrics[3].metric("Energy Bias", f"{delta_percent:+.2f}%")

    monthly_df = pd.DataFrame(
        {
            "Month": MONTH_NAMES,
            "Predicted Energy (kWh)": accuracy_data["predicted_monthly_kwh"],
            "Actual Energy (kWh)": accuracy_data["actual_monthly_kwh"],
        }
    )
    monthly_long = monthly_df.melt(
        id_vars="Month",
        value_vars=["Predicted Energy (kWh)", "Actual Energy (kWh)"],
        var_name="Series",
        value_name="Energy (kWh)",
    )
    energy_chart = px.bar(
        monthly_long,
        x="Month",
        y="Energy (kWh)",
        color="Series",
        barmode="group",
        title="Predicted vs Actual Monthly Energy",
    )
    st.plotly_chart(energy_chart, width="stretch")

    value_df = pd.DataFrame(
        {
            "Month": MONTH_NAMES,
            "Predicted Value": accuracy_data["predicted_monthly_estimated_value"],
            "Actual Value": accuracy_data["actual_monthly_estimated_value"],
        }
    )
    value_long = value_df.melt(
        id_vars="Month",
        value_vars=["Predicted Value", "Actual Value"],
        var_name="Series",
        value_name=f"Value ({assumptions['currency']})",
    )
    value_chart = px.line(
        value_long,
        x="Month",
        y=f"Value ({assumptions['currency']})",
        color="Series",
        markers=True,
        title="Predicted vs Actual Monthly Value",
    )
    value_chart.update_layout(hovermode="x unified")
    st.plotly_chart(value_chart, width="stretch")

    if accuracy_data.get("fallback_reason"):
        st.warning(accuracy_data["fallback_reason"])

    with st.expander("Backtest Metadata", expanded=False):
        metadata_rows = [
            {"Field": "Evaluation year", "Value": accuracy_data["year"]},
            {"Field": "Requested model", "Value": accuracy_data["model_type_requested"]},
            {"Field": "Model used", "Value": accuracy_data["model_type_used"]},
            {
                "Field": "Weather reference year",
                "Value": accuracy_data.get("weather_reference_year") or "ML profile",
            },
            {
                "Field": "ML training years",
                "Value": ", ".join(map(str, accuracy_data.get("training_years_used", [])))
                or "Not used",
            },
        ]
        render_metadata_table(metadata_rows)

        if accuracy_data.get("ml_metadata"):
            st.markdown("**ML diagnostics**")
            st.json(accuracy_data["ml_metadata"])


def render_comparison_tab(
    comparison_data: dict,
    scenario_names: list[str],
) -> None:
    if comparison_data.get("fallback_reason"):
        st.warning(comparison_data["fallback_reason"])

    monthly_chart_rows: list[dict] = []
    for index, result in enumerate(comparison_data["results"]):
        scenario_label = "Base System" if index == 0 else scenario_names[index - 1]
        for month_name, monthly_value in zip(MONTH_NAMES, result["monthly_kwh"]):
            monthly_chart_rows.append(
                {
                    "Month": month_name,
                    "Scenario": scenario_label,
                    "Energy (kWh)": monthly_value,
                }
            )
    monthly_chart_df = pd.DataFrame(monthly_chart_rows)
    monthly_chart = px.line(
        monthly_chart_df,
        x="Month",
        y="Energy (kWh)",
        color="Scenario",
        markers=True,
        title="Scenario Comparison by Month",
    )
    monthly_chart.update_layout(hovermode="x unified")
    st.plotly_chart(monthly_chart, width="stretch")

    summary_rows = []
    for index, result in enumerate(comparison_data["results"]):
        scenario_label = "Base System" if index == 0 else scenario_names[index - 1]
        summary_rows.append(
            {
                "Scenario": scenario_label,
                "Yearly Energy (kWh)": result["yearly_kwh"],
                "Energy Change (%)": result["deviation_percent"],
                "Yearly Value": result["yearly_estimated_value"],
                "Value Change (%)": result["value_deviation_percent"],
            }
        )

    metric_columns = st.columns(len(summary_rows))
    for index, row in enumerate(summary_rows):
        metric_columns[index].metric(
            row["Scenario"],
            f"{row['Yearly Energy (kWh)']} kWh",
            f"{row['Energy Change (%)']:+.2f}%",
        )

    st.dataframe(pd.DataFrame(summary_rows), width="stretch", hide_index=True)


initialize_session_state()

countries = load_country_names()
default_country = "Israel" if "Israel" in countries else countries[0]
current_year = date.today().year
last_complete_year = current_year - 1

st.sidebar.header("Location")
country = st.sidebar.selectbox(
    "Country",
    countries,
    index=countries.index(default_country),
    key="country_select",
)
city = st.sidebar.text_input("City", value="Tel Aviv", key="city_input")
street = st.sidebar.text_input("Street", value="Dizengoff", key="street_input")
number = st.sidebar.text_input("Number", value="100", key="house_number_input")

address = f"{street} {number}, {city}, {country}".strip()
if st.sidebar.button("Locate Address", type="primary"):
    location = geocode_address(address)
    if location:
        st.session_state.lat = location.latitude
        st.session_state.lon = location.longitude
        st.session_state.address = address
        st.success(
            f"Location resolved to {st.session_state.lat:.4f}, {st.session_state.lon:.4f}"
        )
    else:
        st.error("Address could not be resolved. Try a more specific address.")

st.sidebar.markdown("### Detected Address")
if st.session_state.address:
    st.sidebar.info(st.session_state.address)
else:
    st.sidebar.caption("No address selected yet.")

st.sidebar.header("System Parameters")
if st.session_state.pending_panel_area is not None:
    st.session_state.panel_area = st.session_state.pending_panel_area
    st.session_state.pending_panel_area = None

forecast_year = st.sidebar.number_input(
    "Forecast Year",
    min_value=2020,
    max_value=current_year + 2,
    value=current_year,
    step=1,
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
    format_func=lambda value: "Physical baseline" if value == "physical" else "ML baseline",
)
training_years = st.sidebar.slider(
    "ML Training Window (years)",
    min_value=2,
    max_value=5,
    value=3,
    disabled=model_type != "ml",
)
electricity_price_per_kwh = st.sidebar.number_input(
    "Electricity Price / Feed-in Tariff",
    min_value=0.0,
    value=0.17,
    step=0.01,
    format="%.2f",
)
currency = st.sidebar.selectbox("Currency", options=["USD", "EUR", "ILS"], index=0)

with st.sidebar.expander("Advanced Settings", expanded=False):
    panel_efficiency = st.slider("Panel Efficiency", 0.10, 0.30, 0.20)
    tilt = st.slider("Tilt Angle (°)", 0, 60, 30)
    cleanliness = st.selectbox("Panel Cleanliness", ["clean", "normal", "dusty"], index=1)
    shading = st.selectbox("Shading Level", ["none", "low", "medium", "high"], index=1)
    gamma = st.number_input(
        "Temperature Coefficient (gamma)",
        min_value=0.002,
        max_value=0.006,
        value=0.004,
        step=0.0001,
        format="%.4f",
    )
    noct = st.number_input(
        "NOCT (°C)",
        min_value=35.0,
        max_value=60.0,
        value=45.0,
        step=1.0,
    )

run_forecast = st.sidebar.button(
    "Run Alpha Forecast",
    type="primary",
    disabled=st.session_state.lat is None or st.session_state.lon is None,
)

if st.session_state.lat is not None and st.session_state.lon is not None:
    map_object = folium.Map(
        location=[st.session_state.lat, st.session_state.lon],
        zoom_start=18,
    )
    folium.Marker(
        [st.session_state.lat, st.session_state.lon],
        popup=st.session_state.address,
        icon=folium.Icon(icon="home"),
    ).add_to(map_object)
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

    if map_data and map_data.get("all_drawings"):
        last_shape = map_data["all_drawings"][-1]
        drawing_id = last_shape.get("id") or hash(str(last_shape))

        if drawing_id != st.session_state.last_drawing_id:
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
            resolved_address = reverse_geocode(center_lat, center_lon)
            if resolved_address:
                st.session_state.address = resolved_address
            st.session_state.auto_run_forecast = True
            st.success(
                f"Roof area detected: {roof_area:.1f} m². Location and panel area were updated."
            )
            st.rerun()
else:
    st.info("Enter an address to show the map and enable roof selection.")

base_payload = None
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
        training_years=int(training_years),
    )

if run_forecast or st.session_state.auto_run_forecast:
    st.session_state.auto_run_forecast = False
    if base_payload is None:
        st.error("Select a valid location before running the forecast.")
    elif base_payload["panel_area"] <= 0:
        st.error("Panel area must be greater than zero.")
    else:
        with st.spinner("Running yearly forecast and daily simulation..."):
            forecast_response = api_post("/forecast/yearly", base_payload)
            simulation_response = api_post("/simulate", base_payload)
            if forecast_response is not None:
                st.session_state.forecast_data = forecast_response
            if simulation_response is not None:
                st.session_state.daily_simulation = simulation_response
            if forecast_response is not None or simulation_response is not None:
                st.session_state.last_run_payload = dict(base_payload)
            st.session_state.comparison_result = None
            st.session_state.accuracy_result = None

tab_overview, tab_daily, tab_accuracy, tab_scenarios = st.tabs(
    ["Overview", "Daily Simulation", "Accuracy Backtest", "Scenario Comparison"]
)

with tab_overview:
    if st.session_state.forecast_data is None:
        st.info("Run the forecast to see yearly energy, value, and model metadata.")
    else:
        if payload_changed(base_payload, st.session_state.last_run_payload):
            st.warning("Inputs changed after the last run. Click 'Run Alpha Forecast' to refresh the results.")
            render_last_run_summary(st.session_state.last_run_payload)
        render_overview_tab(st.session_state.forecast_data)

with tab_daily:
    if st.session_state.daily_simulation is None:
        st.info("Run the forecast to generate the daily production simulation.")
    else:
        if payload_changed(base_payload, st.session_state.last_run_payload):
            st.warning("Inputs changed after the last run. Click 'Run Alpha Forecast' to refresh the simulation.")
            render_last_run_summary(st.session_state.last_run_payload)
        render_daily_tab(st.session_state.daily_simulation)

with tab_accuracy:
    evaluation_year = min(int(forecast_year), last_complete_year)
    st.caption(
        "Backtest compares the selected forecast model against archived actual weather "
        f"for {evaluation_year}."
    )
    if forecast_year > last_complete_year:
        st.info(
            f"Archived actual weather is only complete through {last_complete_year}, "
            f"so the backtest uses {evaluation_year}."
        )

    if base_payload is None:
        st.info("Select a location and system configuration first.")
    else:
        if st.button("Run Accuracy Backtest", type="primary"):
            accuracy_payload = dict(base_payload)
            accuracy_payload["year"] = evaluation_year
            with st.spinner("Evaluating forecast accuracy against archived data..."):
                accuracy_response = api_post("/evaluation/accuracy", accuracy_payload)
                if accuracy_response is not None:
                    st.session_state.accuracy_result = accuracy_response

        if st.session_state.accuracy_result is None:
            st.info("Run the backtest to compare predicted and actual yearly output.")
        else:
            render_accuracy_tab(st.session_state.accuracy_result)

with tab_scenarios:
    if base_payload is None or st.session_state.forecast_data is None:
        st.info("Run the baseline forecast first to unlock scenario comparison.")
    else:
        top_columns = st.columns([2, 1])
        with top_columns[0]:
            scenario_name = st.text_input(
                "Scenario Name",
                value=f"Scenario {len(st.session_state.scenario_requests) + 1}",
            )
        with top_columns[1]:
            if st.button("Clear All Scenarios"):
                st.session_state.scenario_requests = []
                st.session_state.comparison_result = None
                st.rerun()

        config_columns = st.columns(3)
        with config_columns[0]:
            panel_area_delta_pct = st.slider(
                "Panel Area Change (%)",
                min_value=-50,
                max_value=200,
                value=20,
                step=5,
            )
        with config_columns[1]:
            scenario_tilt = st.slider("Scenario Tilt (°)", 0, 60, int(tilt))
        with config_columns[2]:
            scenario_ac_capacity = st.number_input(
                "Scenario AC Capacity (kW)",
                min_value=0.1,
                value=float(ac_capacity_kw),
            )

        if st.button("Add Scenario", type="primary"):
            scenario_payload = dict(base_payload)
            scenario_payload["panel_area"] = round(
                base_payload["panel_area"] * (1 + panel_area_delta_pct / 100),
                2,
            )
            scenario_payload["tilt"] = int(scenario_tilt)
            scenario_payload["ac_capacity_kw"] = float(scenario_ac_capacity)
            st.session_state.scenario_requests.append(
                {
                    "name": scenario_name,
                    "payload": scenario_payload,
                }
            )
            st.session_state.comparison_result = None
            st.success(f"Scenario '{scenario_name}' added.")

        if st.session_state.scenario_requests:
            if st.button("Run Scenario Comparison"):
                scenario_payloads = [base_payload] + [
                    scenario["payload"] for scenario in st.session_state.scenario_requests
                ]
                with st.spinner("Comparing yearly scenarios..."):
                    comparison_response = api_post("/scenarios/compare", scenario_payloads)
                    if comparison_response is not None:
                        st.session_state.comparison_result = comparison_response

            scenario_table = pd.DataFrame(
                [
                    {
                        "Scenario": scenario["name"],
                        "Panel Area (m²)": scenario["payload"]["panel_area"],
                        "Tilt (°)": scenario["payload"]["tilt"],
                        "AC Capacity (kW)": scenario["payload"]["ac_capacity_kw"],
                    }
                    for scenario in st.session_state.scenario_requests
                ]
            )
            st.dataframe(scenario_table, width="stretch", hide_index=True)

            if st.session_state.comparison_result is not None:
                render_comparison_tab(
                    st.session_state.comparison_result,
                    [scenario["name"] for scenario in st.session_state.scenario_requests],
                )
        else:
            st.info("Add at least one scenario to compare it against the base system.")
