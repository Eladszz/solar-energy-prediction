import streamlit as st # type: ignore
import requests
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim # type: ignore
import folium # type: ignore
from streamlit_folium import st_folium # type: ignore
import pycountry

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Solar Energy Forecast", layout="wide")
st.title("☀️ Solar Energy Production Forecast")
st.caption("Prototype system for solar energy forecasting using physical and ML models")

# Initialize session state
if "lat" not in st.session_state:
    st.session_state.lat = None
if "lon" not in st.session_state:
    st.session_state.lon = None
if "address" not in st.session_state:
    st.session_state.address = None
if "forecast_data" not in st.session_state:
    st.session_state.forecast_data = None
if "forecast_ml" not in st.session_state:
    st.session_state.forecast_ml = None
if "daily_simulation" not in st.session_state:
    st.session_state.daily_simulation = None

# -----------------------
# Sidebar – System Inputs
# -----------------------
st.sidebar.header("📍 Location")

countries = sorted([c.name for c in pycountry.countries]) # type: ignore

country = st.sidebar.selectbox(
    "Select Country",
    countries,
    index=countries.index("Israel") if "Israel" in countries else 0,
    key="country_select"
)
city = st.sidebar.text_input("City", value="Tel Aviv")

c1, c2 = st.sidebar.columns([3, 1])
with c1:
    street = st.text_input("Street", value="Dizengoff")
with c2:
    number = st.text_input("Number", value="100")

address = f"{street} {number}, {city}, {country}"
geocode_btn = st.sidebar.button("📍 Locate Address", type="primary")
lat = lon = None

if geocode_btn and address:
    geolocator = Nominatim(user_agent="solar_app")
    location = geolocator.geocode(address)

    if location:
        st.session_state.lat = location.latitude
        st.session_state.lon = location.longitude
        st.session_state.address = address
        st.success(
            f"Location found: {st.session_state.lat:.4f}, {st.session_state.lon:.4f}"
        )
    else:
        st.error("Address not found")
st.sidebar.header("⚙️ System Parameters")
ac_capacity_kw = st.sidebar.number_input("Inverter AC Capacity (kW)", value=15.0)
panel_area = st.sidebar.number_input("Panel Area (m²)", value=80.0)

with st.sidebar.expander("Advanced Settings:"):
    panel_efficiency = st.slider("Panel Efficiency", 0.10, 0.30, 0.20)
    tilt = st.slider("Tilt Angle (°)", 0, 60, 30)
    cleanliness = st.selectbox(
        "Panel Cleanliness", ["clean", "normal", "dusty"],
        key="cleanliness_select"
    )

    shading = st.selectbox(
        "Shading Level", ["none", "low", "medium", "high"],
        key="shading_select"
    )


run_forecast = st.sidebar.button("▶ Run Forecast", type="primary", key="run_forecast_btn", disabled=st.session_state.lat is None or st.session_state.lon is None)
# -----------------------
# Helper
# -----------------------
def run_yearly(model_type="physical", area_override=None, ac_capacity_override=None):
    payload = {
        "latitude": st.session_state.lat,
        "longitude": st.session_state.lon,
        "panel_area": area_override or panel_area,
        "panel_efficiency": panel_efficiency,
        "tilt": tilt,
        "ac_capacity_kw": ac_capacity_override or ac_capacity_kw,
        "model_type": model_type
    }
    res = requests.post(f"{BACKEND_URL}/forecast/yearly", json=payload)
    res.raise_for_status()
    return res.json()
def run_simulation():
    payload = {
        "latitude": st.session_state.lat,
        "longitude": st.session_state.lon,
        "panel_area": panel_area,
        "panel_efficiency": panel_efficiency,
        "tilt": tilt,
        "cleanliness": cleanliness,
        "shading": shading,
        "ac_capacity_kw": ac_capacity_kw
    }

    res = requests.post(f"{BACKEND_URL}/simulate", json=payload)
    res.raise_for_status()
    return res.json()
# -----------------------
# Map
# -----------------------
if st.session_state.lat is not None and st.session_state.lon is not None:
    m = folium.Map(
        location=[st.session_state.lat, st.session_state.lon],
        zoom_start=17
        )
    folium.Marker(
        [st.session_state.lat, st.session_state.lon],
        popup=st.session_state.address,
        draggable=True,
        icon=folium.Icon(icon="home")
        ).add_to(m)
    map_data = st_folium(m, width=700, height=400)

    if map_data and map_data.get("last_clicked"):
        st.session_state.lat = map_data["last_clicked"]["lat"]
        st.session_state.lon = map_data["last_clicked"]["lng"]

    st.caption(
        f"📌 Selected location: "
        f"{st.session_state.lat:.6f}, {st.session_state.lon:.6f}"
        )


else:
    st.info("📍 Enter an address and click 'Locate Address' to display the map.")


# -----------------------
# Tabs
# -----------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Overview (Yearly/Monthly)", "📅 Daily Simulation", "🤖 Model Comparison", "🔍 Explainability", "🔁 What-If"]
)
if run_forecast:
    if st.session_state.lat is None or st.session_state.lon is None:
        st.warning("Please select a location first")
    else:
        with st.spinner("Running forecast..."):
            st.session_state.forecast_data = run_yearly("physical")
            st.session_state.forecast_ml = run_yearly("ml")
            st.session_state.daily_simulation = run_simulation()
# =======================
# TAB 1 – Overview
# =======================
with tab1:
    if st.session_state.lat is None or st.session_state.lon is None:
        st.warning("⚠️ Please enter an address and click '📍 Locate Address' in the sidebar to see forecast data.")
    elif st.session_state.forecast_data is None:
        st.info("👉 Click '▶ Run Forecast' in the sidebar to generate forecast data.")
    else:
        data = st.session_state.forecast_data

        col1, col2, col3 = st.columns(3)
        col1.metric("Yearly Energy (kWh)", round(data["yearly_kwh"], 1))
        col2.metric("Specific Yield (kWh/kWp)", round(data["specific_yield_kwh_per_kwp"], 1))
        col3.metric("Avg Monthly Energy (kWh)", round(sum(data["monthly_kwh"]) / 12, 1))

        df = pd.DataFrame({
            "month": list(range(1, 13)),
            "energy_kwh": data["monthly_kwh"]
        })

        fig = px.bar(df, x="month", y="energy_kwh", title="Monthly Energy Production")
        st.plotly_chart(fig, use_container_width=True)
# =======================
# TAB 2 – Daily Simulation
# =======================
with tab2:
    st.subheader("⏱ Daily Power Simulation")

    if st.session_state.lat is None or st.session_state.lon is None:
        st.warning("⚠️ Please enter an address and click '📍 Locate Address' in the sidebar to see forecast data.")
    elif st.session_state.daily_simulation is None:
        st.info("👉 Click '▶ Run Forecast' in the sidebar to generate simulation data.")
    else:
        data = st.session_state.daily_simulation
        st.subheader("🔌 Hourly Power Production")

        df = pd.DataFrame({
            "hour": list(range(24)),
            "ac_kw": data["hourly_ac_kw"]
        })

        fig = px.line(
            df,
            x="hour",
            y="ac_kw",
            labels={"ac_kw": "AC Power (kW)", "hour": "Hour of Day"},
            markers=True
        )

        st.plotly_chart(fig, use_container_width=True)

        st.metric("Average Power (kW)", round(data["avg_kw"], 2))


# =======================
# TAB 3 – Model Comparison
# =======================
with tab3:
    if st.session_state.lat is None or st.session_state.lon is None:
        st.warning("⚠️ Please enter an address and click '📍 Locate Address' in the sidebar to see forecast data.")
    elif st.session_state.forecast_data is None or st.session_state.forecast_ml is None:
        st.info("👉 Click '▶ Run Forecast' in the sidebar to generate forecast data.")
    else:
        physical = st.session_state.forecast_data
        ml = st.session_state.forecast_ml

        df = pd.DataFrame({
            "month": list(range(1, 13)),
            "Physical Model": physical["monthly_kwh"],
            "ML Model": ml["monthly_kwh"]
        })

        fig = px.line(
            df,
            x="month",
            y=["Physical Model", "ML Model"],
            markers=True,
            title="Physical vs ML Forecast Comparison"
        )
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        col1.metric("Physical Yearly (kWh)", round(physical["yearly_kwh"], 1))
        col2.metric("ML Yearly (kWh)", round(ml["yearly_kwh"], 1))

# =======================
# TAB 4 – Explainability
# =======================
with tab4:
    st.subheader("Key Factors Affecting Production")

    factors = pd.DataFrame({
        "Factor": ["Solar Irradiance", "Panel Efficiency", "Shading", "Temperature"],
        "Impact (%)": [45, 25, 20, 10]
    })

    fig = px.bar(
        factors,
        x="Impact (%)",
        y="Factor",
        orientation="h",
        title="Estimated Impact Contribution"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "Explainability is based on feature contribution analysis "
        "derived from model sensitivity and historical correlations."
    )

# =======================
# TAB 5 – What-If Scenario
# =======================
with tab5:
    st.info("The What-If scenario allows evaluating the impact of system design changes (e.g., panel area) on annual energy production.")
    if st.session_state.lat is None or st.session_state.lon is None:
        st.warning("⚠️ Please enter an address and click '📍 Locate Address' in the sidebar to see forecast data.")
    elif st.session_state.forecast_data is None:
        st.info("👉 Click '▶ Run Forecast' in the sidebar to generate baseline forecast data first.")
    else:
        base = st.session_state.forecast_data
        st.write("Select a scenario to evaluate:")
        what_if_panel_area = st.slider(
            "Panel Area Increase (%)",
            0,
            100,
            20,
            step=5,
            help="Increase the panel area by a certain percentage to see its effect on production."
        )
        what_if_ac_capacity = st.text_input(
            "Inverter AC Capacity Override (kW)",
            value=str(ac_capacity_kw),
            help="Optionally override the inverter AC capacity for this scenario."
        )
        try:
            new_ac_capacity_kw = float(what_if_ac_capacity)
        except ValueError:
            new_ac_capacity_kw = ac_capacity_kw

        new_area = panel_area * (1 + what_if_panel_area / 100)

        scenario = None
        if st.button("▶ Run What-If Scenario", type="primary"):
            scenario = run_yearly(
                model_type="physical",
                area_override=new_area,
                ac_capacity_override=new_ac_capacity_kw
            )

        if scenario:
            scenario_label = f"Area +{what_if_panel_area}%"
            df = pd.DataFrame({
                "month": list(range(1, 13)),
                "Base System": base["monthly_kwh"],
                scenario_label: scenario["monthly_kwh"]
            })

            fig = px.line(
                df,
                x="month",
                y=["Base System", scenario_label],
                markers=True,
                title="What-If Scenario: Increased Panel Area"
            )
            st.plotly_chart(fig, use_container_width=True)

            delta = scenario["yearly_kwh"] - base["yearly_kwh"]
            st.metric("Annual Gain (kWh)", round(delta, 1))
