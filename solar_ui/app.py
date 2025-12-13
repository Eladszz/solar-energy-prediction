import streamlit as st
import requests
import pandas as pd
import plotly.express as px

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Solar Energy Forecast",
    layout="wide"
)

st.title("☀️ Solar Energy Production Forecast")

st.markdown(
    "Prototype dashboard for simulating and forecasting solar energy production."
)

# --------------------
# Sidebar – Inputs
# --------------------
st.sidebar.header("System Parameters")

latitude = st.sidebar.number_input("Latitude", value=32.08, format="%.4f")
longitude = st.sidebar.number_input("Longitude", value=34.78, format="%.4f")

panel_area = st.sidebar.number_input("System Area (m²)", value=80.0)
panel_efficiency = st.sidebar.slider("Panel Efficiency", 0.10, 0.30, 0.20)

tilt = st.sidebar.slider("Tilt Angle (°)", 0, 60, 30)

cleanliness = st.sidebar.selectbox(
    "Panel Cleanliness", ["clean", "normal", "dusty"]
)

shading = st.sidebar.selectbox(
    "Shading Level", ["none", "low", "medium", "high"]
)

ac_capacity_kw = st.sidebar.number_input(
    "Inverter AC Capacity (kW)",
    value=15.0
)

# --------------------
# Buttons
# --------------------
col1, col2 = st.columns(2)

run_daily = col1.button("🔄 Run Daily Simulation")
run_yearly = col2.button("📅 Run Yearly Forecast")


def run_simulation():
    payload = {
        "latitude": latitude,
        "longitude": longitude,
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


if run_daily:
    with st.spinner("Running daily simulation..."):
        data = run_simulation()

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


def run_yearly_forecast():
    payload = {
        "latitude": latitude,
        "longitude": longitude,
        "panel_area": panel_area,
        "panel_efficiency": panel_efficiency,
        "tilt": tilt,
        "cleanliness": cleanliness,
        "shading": shading,
        "ac_capacity_kw": ac_capacity_kw
    }

    res = requests.post(f"{BACKEND_URL}/forecast/yearly", json=payload)
    res.raise_for_status()
    return res.json()


if run_yearly:
    with st.spinner("Running yearly forecast..."):
        data = run_yearly_forecast()

    st.subheader("📊 Monthly Energy Production")

    months = list(range(1, 13))
    df = pd.DataFrame({
        "month": months,
        "kwh": data["monthly_kwh"]
    })

    fig = px.bar(
        df,
        x="month",
        y="kwh",
        labels={"kwh": "Energy (kWh)", "month": "Month"}
    )

    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    col1.metric("Yearly Energy (kWh)", round(data["yearly_kwh"], 1))
    col2.metric(
        "Specific Yield (kWh/kWp)",
        round(data["specific_yield_kwh_per_kwp"], 1)
    )
