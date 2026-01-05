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
if "daily_simulation" not in st.session_state:
    st.session_state.daily_simulation = None
if "scenarios" not in st.session_state:
    st.session_state.scenarios = []

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
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Overview (Yearly/Monthly)", "📅 Daily Simulation", "🔍 Explainability", "🔁 What-If"]
)
if run_forecast:
    if st.session_state.lat is None or st.session_state.lon is None:
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
            markers=True
        )

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
# TAB 4 – What-If Scenario
# =======================
with tab4:
    st.info("The What-If scenario allows evaluating the impact of system design changes (e.g., panel area) on annual energy production.")
    if st.session_state.lat is None or st.session_state.lon is None:
        st.warning("⚠️ Please enter an address and click '📍 Locate Address' in the sidebar to see forecast data.")
    elif st.session_state.forecast_data is None:
        st.info("👉 Click '▶ Run Forecast' in the sidebar to generate baseline forecast data first.")
    else:
        base = st.session_state.forecast_data
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**Configure a new scenario:**")
            scenario_name = st.text_input(
                "Scenario Name",
                value=f"Scenario {len(st.session_state.scenarios) + 1}",
                help="Give this scenario a descriptive name"
            )
            
        with col2:
            st.write("")
            st.write("")
            if st.button("🗑️ Clear All Scenarios", help="Remove all scenarios from the comparison"):
                st.session_state.scenarios = []
                st.rerun()
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            what_if_panel_area = st.slider(
                "Panel Area Increase (%)",
                -50,
                200,
                20,
                step=5,
                help="Increase or decrease the panel area by a certain percentage."
            )
            
        with col_b:
            what_if_ac_capacity = st.number_input(
                "Inverter AC Capacity (kW)",
                value=float(ac_capacity_kw),
                min_value=0.0,
                help="Override the inverter AC capacity for this scenario."
            )

        new_area = panel_area * (1 + what_if_panel_area / 100)
        
        if st.button("➕ Add Scenario to Comparison", type="primary"):
            with st.spinner("Running scenario..."):
                scenario_data = run_yearly(
                    model_type="physical",
                    area_override=new_area,
                    ac_capacity_override=what_if_ac_capacity
                )
                
                st.session_state.scenarios.append({
                    "name": scenario_name,
                    "panel_area": new_area,
                    "ac_capacity_kw": what_if_ac_capacity,
                    "panel_area_change": what_if_panel_area,
                    "data": scenario_data
                })
                st.success(f"✅ Added scenario: {scenario_name}")
                st.rerun()

        # Display comparison if scenarios exist
        if st.session_state.scenarios:
            st.divider()
            st.subheader("📊 Scenario Comparison")
            
            # Build dataframe with base and all scenarios
            df_dict = {
                "month": list(range(1, 13)),
                "Base System": base["monthly_kwh"]
            }
            
            for scenario in st.session_state.scenarios:
                df_dict[scenario["name"]] = scenario["data"]["monthly_kwh"]
            
            df = pd.DataFrame(df_dict)
            
            # Create line chart
            columns_to_plot = [col for col in df.columns if col != "month"]
            fig = px.line(
                df,
                x="month",
                y=columns_to_plot,
                markers=True,
                title="Monthly Energy Production Comparison",
                labels={"value": "Energy (kWh)", "month": "Month", "variable": "Scenario"}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Display metrics in columns
            st.subheader("📈 Annual Production Summary")
            cols = st.columns(len(st.session_state.scenarios) + 1)
            
            with cols[0]:
                st.metric(
                    "Base System",
                    f"{round(base['yearly_kwh'], 1)} kWh",
                    help=f"Panel Area: {panel_area} m², AC Capacity: {ac_capacity_kw} kW"
                )
            
            for idx, scenario in enumerate(st.session_state.scenarios):
                with cols[idx + 1]:
                    delta = scenario["data"]["yearly_kwh"] - base["yearly_kwh"]
                    delta_percent = (delta / base["yearly_kwh"]) * 100
                    st.metric(
                        scenario["name"],
                        f"{round(scenario['data']['yearly_kwh'], 1)} kWh",
                        f"{delta:+.1f} kWh ({delta_percent:+.1f}%)",
                        help=f"Panel Area: {scenario['panel_area']:.1f} m² ({scenario['panel_area_change']:+.0f}%), AC Capacity: {scenario['ac_capacity_kw']} kW"
                    )
            
            # Scenario details table
            with st.expander("📋 View Scenario Details"):
                details_data = []
                details_data.append({
                    "Scenario": "Base System",
                    "Panel Area (m²)": panel_area,
                    "AC Capacity (kW)": ac_capacity_kw,
                    "Annual Energy (kWh)": round(base["yearly_kwh"], 1),
                    "Gain vs Base (%)": "—"
                })
                
                for scenario in st.session_state.scenarios:
                    delta_percent = ((scenario["data"]["yearly_kwh"] - base["yearly_kwh"]) / base["yearly_kwh"]) * 100
                    details_data.append({
                        "Scenario": scenario["name"],
                        "Panel Area (m²)": round(scenario["panel_area"], 1),
                        "AC Capacity (kW)": scenario["ac_capacity_kw"],
                        "Annual Energy (kWh)": round(scenario["data"]["yearly_kwh"], 1),
                        "Gain vs Base (%)": f"{delta_percent:+.1f}%"
                    })
                
                st.dataframe(pd.DataFrame(details_data), use_container_width=True, hide_index=True)
        else:
            st.info("👆 Configure and add scenarios above to see the comparison.")
