from __future__ import annotations

from typing import Iterable


def estimate_energy_value(
    energy_kwh: float,
    electricity_price_per_kwh: float,
) -> float:
    return round(max(energy_kwh, 0.0) * electricity_price_per_kwh, 2)


def build_financial_summary(
    monthly_kwh: Iterable[float],
    electricity_price_per_kwh: float,
    currency: str,
) -> dict:
    monthly_kwh_list = [round(float(value), 1) for value in monthly_kwh]
    monthly_estimated_value = [
        estimate_energy_value(value, electricity_price_per_kwh)
        for value in monthly_kwh_list
    ]
    yearly_kwh = round(sum(monthly_kwh_list), 1)
    yearly_estimated_value = round(sum(monthly_estimated_value), 2)

    return {
        "monthly_estimated_value": monthly_estimated_value,
        "yearly_estimated_value": yearly_estimated_value,
        "avg_monthly_estimated_value": round(yearly_estimated_value / 12, 2),
        "financial_assumptions": {
            "electricity_price_per_kwh": round(electricity_price_per_kwh, 4),
            "currency": currency,
            "valuation_basis": "Estimated self-consumption or feed-in value from forecasted energy.",
        },
        "yearly_kwh": yearly_kwh,
    }
