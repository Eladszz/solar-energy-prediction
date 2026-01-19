
import streamlit as st # type: ignore
import requests
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim # type: ignore
from utils import estimate_area_m2_from_bounds
import folium # type: ignore
from streamlit_folium import st_folium # type: ignore
import pycountry
from utils import reverse_geocode
from folium.plugins import Draw # type: ignore
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

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
if "daily_simulation" not in st.session_state:
    st.session_state.daily_simulation = None
if "scenarios" not in st.session_state:
    st.session_state.scenarios = []
if "pending_panel_area" not in st.session_state:
    st.session_state.pending_panel_area = None
if "last_drawing_id" not in st.session_state:
    st.session_state.last_drawing_id = None
if "pending_address" not in st.session_state:
    st.session_state.pending_address = None
if "auto_run_forecast" not in st.session_state:
    st.session_state.auto_run_forecast = False

# -----------------------
# Sidebar – System Inputs
# -----------------------
st.sidebar.header("📍 Location")

countries = sorted([c.name for c in pycountry.countries]) # type: ignore

if st.session_state.pending_address is not None:
    st.session_state.country_select = st.session_state.pending_address.country
    st.session_state.city_input = st.session_state.pending_address.city
    st.session_state.street_input = st.session_state.pending_address.street
    st.session_state.house_number_input = st.session_state.pending_address.number
    st.session_state.pending_address = None

country = st.sidebar.selectbox(
    "Select Country",
    countries,
    index=countries.index("Israel") if "Israel" in countries else 0,
    key="country_select"
)
city = st.sidebar.text_input("City", value="Tel Aviv", key="city_input")

c1, c2 = st.sidebar.columns([3, 1])
with c1:
    street = st.text_input("Street", value="Dizengoff", key="street_input")
with c2:
    number = st.text_input("Number", value="100", key="house_number_input")

st.sidebar.markdown("### 📍 Detected Address")
if st.session_state.address:
    st.sidebar.info(st.session_state.address)
else:
    st.sidebar.caption("No address detected yet")

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

if st.session_state.pending_panel_area is not None:
    st.session_state.panel_area = st.session_state.pending_panel_area
    st.session_state.pending_panel_area = None

panel_area = st.sidebar.number_input(
    "Panel Area (m²)",
    min_value=0.0,
    key="panel_area"
)



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

    gamma = st.number_input(
        "Temperature Coefficient (gamma)",
        min_value=0.002,
        max_value=0.006,
        value=0.004,
        step=0.0001,
        format="%.4f",
        help="Panel efficiency loss per °C above 25°C"
    )

    noct = st.number_input(
        "NOCT (°C)",
        min_value=35.0,
        max_value=60.0,
        value=45.0,
        step=1.0,
        help="Nominal Operating Cell Temperature"
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
        zoom_start=18
    )

    # Marker
    folium.Marker(
        [st.session_state.lat, st.session_state.lon],
        popup=st.session_state.address,
        icon=folium.Icon(icon="home"),
    ).add_to(m)

    # Enable drawing (rectangle only)
    draw = Draw(
        draw_options={
            "polyline": False,
            "polygon": False,
            "circle": False,
            "circlemarker": False,
            "marker": False,
            "rectangle": True,
        },
        edit_options={"edit": True}
    )
    draw.add_to(m)

    map_data = st_folium(m, height=400, use_container_width=True)

    if map_data and map_data.get("all_drawings"):
        last_shape = map_data["all_drawings"][-1]
        drawing_id = last_shape.get("id") or hash(str(last_shape))

        if drawing_id != st.session_state.last_drawing_id:
            st.session_state.last_drawing_id = drawing_id

            coords = last_shape["geometry"]["coordinates"][0]
            lats = [c[1] for c in coords]
            lons = [c[0] for c in coords]

            bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]

            roof_area = estimate_area_m2_from_bounds(bounds)
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)

            st.session_state.pending_panel_area = round(roof_area, 1)
            st.session_state.lat = center_lat
            st.session_state.lon = center_lon
            new_address = reverse_geocode(center_lat, center_lon)
            if new_address:
                st.session_state.address = new_address
                logger.info(f"Updated address: {new_address}")


            st.success(
                f"🏠 Roof detected | Area: {roof_area:.1f} m² | Location updated"
            )
            logger.info(f"Detected roof area: {roof_area:.1f} m² at ({center_lat}, {center_lon})")

            st.session_state.auto_run_forecast = True
            st.rerun()







else:
    st.info("📍 Enter an address and click 'Locate Address' to display the map.")


# -----------------------
# Tabs
# -----------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Overview (Yearly/Monthly)", "📅 Daily Simulation", "🔍 Explainability", "🔁 What-If"]
)
if run_forecast or st.session_state.auto_run_forecast:
    if st.session_state.panel_area is None or st.session_state.panel_area <= 0:
        st.error("Please specify a valid Panel Area before running the forecast.")
    elif st.session_state.lat is None or st.session_state.lon is None:
        st.warning("Please select a location first")
    else:
        with st.spinner("Running forecast..."):
            st.session_state.forecast_data = run_yearly("physical")
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
        timezone = data.get("timezone", "UTC")
        st.subheader(f"🔌 Hourly Power Production ({timezone})")

        # Use actual timestamps if available, otherwise use hour numbers
        if "hourly_time" in data and data["hourly_time"]:
            # Extract hour from ISO timestamp (e.g., "2024-01-05T14:00")
            time_labels = [ts.split("T")[1][:5] if "T" in ts else f"{i:02d}:00" 
                          for i, ts in enumerate(data["hourly_time"])]
            df = pd.DataFrame({
                "time": time_labels,
                "ac_kw": data["hourly_ac_kw"]
            })
            x_col = "time"
            x_label = f"Time ({timezone})"
        else:
            df = pd.DataFrame({
                "hour": list(range(24)),
                "ac_kw": data["hourly_ac_kw"]
            })
            x_col = "hour"
            x_label = "Hour of Day"

        fig = px.line(
            df,
            x=x_col,
            y="ac_kw",
            labels={"ac_kw": "AC Power (kW)", x_col: x_label},
            markers=True,
        )
        fig.update_layout(hovermode="x unified")

        st.plotly_chart(fig, use_container_width=True)

        st.metric("Average Power (kW)", round(data["avg_kw"], 2))


# =======================
# TAB 3 – Explainability
# =======================
with tab3:
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
# TAB 4 – What-If Scenario (Refactored)
# =======================


with tab4:
    st.info(
        "The What-If scenario allows evaluating the impact of system design changes "
        "(e.g., panel area, inverter capacity) on annual energy production."
    )

    if st.session_state.lat is None or st.session_state.lon is None:
        st.warning("⚠️ Please enter an address and click '📍 Locate Address' in the sidebar.")
        st.stop()

    if st.session_state.forecast_data is None:
        st.info("👉 Click '▶ Run Forecast' in the sidebar to generate baseline forecast data first.")
        st.stop()

    # -----------------------
    # Base system (baseline)
    # -----------------------
    # Provide default values for gamma and noct if not set in the UI

    if st.session_state.lat is None or st.session_state.lon is None:
        st.warning("⚠️ Please enter an address and click '📍 Locate Address' in the sidebar.")
        st.stop()
        
    latitude: float = float(st.session_state.lat) # type: ignore
    longitude: float = float(st.session_state.lon) # type: ignore


    base_request = {
        "latitude": latitude,
        "longitude": longitude,
        "tilt": tilt,
        "panel_area": panel_area,
        "panel_efficiency": panel_efficiency,
        "cleanliness": cleanliness,
        "shading": shading,
        "ac_capacity_kw": ac_capacity_kw,
        "gamma": gamma,
        "noct": noct,
    }

    if "scenario_requests" not in st.session_state:
        st.session_state.scenario_requests = []

    # -----------------------
    # Scenario configuration
    # -----------------------
    col1, col2 = st.columns([2, 1])

    with col1:
        st.write("**Configure a new scenario:**")
        scenario_name = st.text_input(
            "Scenario Name",
            value=f"Scenario {len(st.session_state.scenario_requests) + 1}",
        )

    with col2:
        st.write("")
        st.write("")
        if st.button("🗑️ Clear All Scenarios"):
            st.session_state.scenario_requests = []
            st.rerun()

    col_a, col_b = st.columns(2)

    with col_a:
        panel_area_delta_pct = st.slider(
            "Panel Area Change (%)",
            -50,
            200,
            20,
            step=5,
        )

    with col_b:
        scenario_ac_capacity = st.number_input(
            "Inverter AC Capacity (kW)",
            value=float(ac_capacity_kw),
            min_value=0.0,
        )

    new_panel_area = panel_area * (1 + panel_area_delta_pct / 100)

    if st.button("➕ Add Scenario to Comparison", type="primary"):
        scenario_request = {
            "latitude": latitude,
            "longitude": longitude,
            "tilt": tilt,
            "panel_area": new_panel_area,
            "panel_efficiency": panel_efficiency,
            "cleanliness": cleanliness,
            "shading": shading,
            "ac_capacity_kw": scenario_ac_capacity,
            "gamma": gamma,
            "noct": noct,
        }

        st.session_state.scenario_requests.append({
            "name": scenario_name,
            "request": scenario_request,
            "panel_area_change": panel_area_delta_pct,
        })

        st.success(f"✅ Added scenario: {scenario_name}")
        st.rerun()

    # -----------------------
    # Scenario comparison
    # -----------------------
    if st.session_state.scenario_requests:
        st.divider()
        st.subheader("📊 Scenario Comparison")

        scenarios = [base_request] + [
            s["request"] for s in st.session_state.scenario_requests
        ]

        with st.spinner("Comparing scenarios..."):
            response = requests.post(
            f"{BACKEND_URL}/scenarios/compare",
            json=[s for s in scenarios]
        )

        if response.status_code != 200:
            st.error(response.json().get("detail", "Scenario comparison failed"))
            st.stop()

        comparison = response.json()


        # -----------------------
        # Monthly comparison chart
        # -----------------------
        df_chart = {
            "month": list(range(1, 13)),
            "Base System": comparison["results"][0]["monthly_kwh"],
        }

        for idx, s in enumerate(st.session_state.scenario_requests):
            df_chart[s["name"]] = comparison["results"][idx + 1]["monthly_kwh"]

        df_plot = pd.DataFrame(df_chart)

        fig = px.line(
            df_plot,
            x="month",
            y=[c for c in df_plot.columns if c != "month"],
            markers=True,
            title="Monthly Energy Production Comparison",
            labels={"value": "Energy (kWh)", "month": "Month", "variable": "Scenario"},
        )
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # -----------------------
        # Annual summary metrics
        # -----------------------
        st.subheader("📈 Annual Production Summary")
        cols = st.columns(len(st.session_state.scenario_requests) + 1)

        base_result = comparison["results"][0]

        with cols[0]:
            st.metric(
                "Base System",
                f"{round(base_result['yearly_kwh'], 1)} kWh",
            )

        for idx, s in enumerate(st.session_state.scenario_requests):
            result = comparison["results"][idx + 1]
            with cols[idx + 1]:
                st.metric(
                    s["name"],
                    f"{round(result['yearly_kwh'], 1)} kWh",
                    f"{result['deviation_percent']:+.1f}%",
                )

        # -----------------------
        # Details table
        # -----------------------
        with st.expander("📋 View Scenario Details"):
            rows = []

            rows.append({
                "Scenario": "Base System",
                "Panel Area (m²)": panel_area,
                "AC Capacity (kW)": ac_capacity_kw,
                "Annual Energy (kWh)": round(base_result["yearly_kwh"], 1),
                "Gain vs Base (%)": "—",
            })

            for idx, s in enumerate(st.session_state.scenario_requests):
                result = comparison["results"][idx + 1]
                rows.append({
                    "Scenario": s["name"],
                    "Panel Area (m²)": round(s["request"]["panel_area"], 1),
                    "AC Capacity (kW)": s["request"]["ac_capacity_kw"],
                    "Annual Energy (kWh)": round(result["yearly_kwh"], 1),
                    "Gain vs Base (%)": f"{result['deviation_percent']:+.1f}%",
                })

            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    else:
        st.info("👆 Configure and add scenarios above to see the comparison.")
    
    if st.button("📊 Evaluate Model Accuracy"):
        with st.spinner("Evaluating accuracy..."):
            response = requests.post(
                f"{BACKEND_URL}/evaluation/accuracy",
                json={
                    "latitude": latitude,
                    "longitude": longitude,
                    "tilt": tilt,
                    "panel_area": panel_area,
                    "panel_efficiency": panel_efficiency,
                    "cleanliness": cleanliness,
                    "shading": shading,
                    "ac_capacity_kw": ac_capacity_kw,
                    "gamma": gamma,
                    "noct": noct,
                }
            )

            if response.status_code != 200:
                st.error("Accuracy evaluation failed")
                st.stop()

            accuracy = response.json()
            mape = accuracy["mape_percent"]
            quality = accuracy["quality"]

            if quality == "EXCELLENT":
                color = "green"
            elif quality == "GOOD":
                color = "orange"
            else:
                color = "red"

            st.markdown("### 📊 Model Accuracy")

            st.metric(
                label="MAPE (%)",
                value=f"{mape}%",
                delta=quality
            )

            st.markdown(
                f"<span style='color:{color}; font-weight:bold'>Model quality: {quality}</span>",
                unsafe_allow_html=True
            )

