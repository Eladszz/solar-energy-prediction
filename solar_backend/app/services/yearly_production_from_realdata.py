from app.services.simulation_service import simulate_production_enhanced
import pandas as pd

def compute_yearly_from_real_data(
    df,
    latitude,
    tilt,
    panel_area,
    efficiency,
    gamma,
    noct
):
    irr_list = df["irr"].tolist()
    temp_list = df["temp"].tolist()

    hourly_kw = simulate_production_enhanced(
        irradiance_list=irr_list,
        temp_list=temp_list,
        latitude=latitude,
        tilt=tilt,
        panel_area=panel_area,
        efficiency=efficiency,
        gamma=gamma,
        noct=noct
    )

    df["kw"] = hourly_kw
    df["kwh"] = df["kw"]  # Because each row = 1 hour

    df["month"] = df["time"].dt.month

    monthly = df.groupby("month")["kwh"].sum().tolist()
    yearly = sum(monthly)

    return {
        "monthly_kwh": monthly,
        "yearly_kwh": yearly
    }
