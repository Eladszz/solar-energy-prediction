from app.services.weather_archive_service import get_year_archive
from app.services.yearly_forecast_service import compute_yearly_from_real_data
from app.services.loss_service import compute_system_loss_factor


def calculate_mape(actual: float, predicted: float) -> float:
    if actual == 0:
        return 0.0
    return abs((actual - predicted) / actual) * 100


def evaluate_yearly_accuracy(
    latitude: float,
    longitude: float,
    year: int,
    tilt: float,
    panel_area: float,
    efficiency: float,
    cleanliness: str,
    shading: str,
    gamma: float,
    noct: float,
    ac_capacity_kw: float,
) -> dict:
    """
    Evaluate forecast accuracy using MAPE.
    """

    # 1. Load historical weather
    df = get_year_archive(latitude, longitude, year)

    # 2. System loss
    system_loss_factor = compute_system_loss_factor(
        cleanliness=cleanliness,
        shading=shading
    )

    # 3. Run simulation (prediction)
    forecast = compute_yearly_from_real_data(
        df=df.copy(),
        latitude=latitude,
        tilt=tilt,
        panel_area=panel_area,
        efficiency=efficiency,
        gamma=gamma,
        noct=noct,
        system_loss_factor=system_loss_factor,
        ac_capacity_kw=ac_capacity_kw
    )

    predicted_yearly = forecast["yearly_kwh"]

    # 4. “Actual” yearly energy (baseline from same data)
    actual_yearly = df["irr"].sum() * panel_area * efficiency / 1000  # simplified baseline

    # 5. Accuracy metric
    mape = calculate_mape(actual_yearly, predicted_yearly)

    # 6. Qualitative label (for presentation)
    if mape < 10:
        quality = "EXCELLENT"
    elif mape < 25:
        quality = "GOOD"
    else:
        quality = "POOR"

    return {
        "year": year,
        "actual_yearly_kwh": round(actual_yearly, 1),
        "predicted_yearly_kwh": round(predicted_yearly, 1),
        "mape_percent": round(mape, 2),
        "quality": quality
    }
