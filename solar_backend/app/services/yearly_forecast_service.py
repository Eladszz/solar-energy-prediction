from app.services.simulation_service import simulate_production_enhanced
import logging
logger = logging.getLogger(__name__)

def compute_yearly_from_real_data(
    df,
    latitude,
    tilt,
    panel_area,
    efficiency,
    gamma,
    noct,
    system_loss_factor=0.87
):
    irr_list = df["irr"].tolist()
    temp_list = df["temp"].tolist()
    logger.info("Starting yearly production computation from real data...")
    hourly_kw = simulate_production_enhanced(
        irradiance_list=irr_list,
        temp_list=temp_list,
        latitude=latitude,
        tilt=tilt,
        panel_area=panel_area,
        efficiency=efficiency,
        gamma=gamma,
        noct=noct,
        system_loss_factor=system_loss_factor
    )

    df["kw"] = hourly_kw
    df["kwh"] = df["kw"]  # Because each row = 1 hour
    df["month"] = df["time"].dt.month
    logger.info("Aggregating monthly and yearly production data...")
    monthly = df.groupby("month")["kwh"].sum().tolist()
    yearly = sum(monthly)
    logger.info(f"Monthly production data: {monthly}")
    dc_capacity_kwp = panel_area * efficiency
    specific_yield = yearly / dc_capacity_kwp
    avg_daily_kwh = yearly / 365

    logger.info(f"Yearly production computed: yearly_kwh={yearly}, specific_yield_kwh_per_kwp={specific_yield}, avg_daily_kwh={avg_daily_kwh}")
    return {
        "monthly_kwh": monthly,
        "yearly_kwh": round(yearly, 1),
        "specific_yield_kwh_per_kwp": round(specific_yield, 1),
        "avg_daily_kwh": round(avg_daily_kwh, 1)
    }

