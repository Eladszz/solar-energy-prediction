from typing import List, Dict
from app.models.pv_models import BasePVRequest
from app.services.weather_archive_service import get_year_archive
from app.services.yearly_forecast_service import compute_yearly_from_real_data
from app.services.loss_service import compute_system_loss_factor
import pandas as pd


def compare_yearly_scenarios(
    latitude: float,
    longitude: float,
    scenarios: List[BasePVRequest],
) -> Dict:
    """
    Use Case 6.2.2 – Yearly Scenario Comparison
    """

    year = pd.Timestamp.now().year - 1

    # 1. Fetch historical weather ONCE
    df = get_year_archive(latitude, longitude, year)

    results = []

    for scenario in scenarios:
        system_loss_factor = compute_system_loss_factor(
            cleanliness=scenario.cleanliness,
            shading=scenario.shading
        )

        forecast = compute_yearly_from_real_data(
            df=df.copy(),
            latitude=latitude,
            tilt=scenario.tilt,
            panel_area=scenario.panel_area,
            efficiency=scenario.panel_efficiency,
            gamma=scenario.gamma,
            noct=scenario.noct,
            system_loss_factor=system_loss_factor,
            ac_capacity_kw=scenario.ac_capacity_kw,
        )

        results.append({
            "scenario": scenario,
            "yearly_kwh": forecast["yearly_kwh"],
            "monthly_kwh": forecast["monthly_kwh"],
        })

    baseline = results[0]["yearly_kwh"]

    for r in results:
        r["deviation_percent"] = round(
            100 * (r["yearly_kwh"] - baseline) / baseline, 2
        )

    return {
        "year": year,
        "baseline_yearly_kwh": baseline,
        "results": results,
    }
