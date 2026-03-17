from __future__ import annotations

from typing import Iterable


def calculate_simple_payback_years(
    system_capex: float,
    annual_savings: float,
) -> float | None:
    if annual_savings <= 0.0:
        return None
    return round(max(system_capex, 0.0) / annual_savings, 1)


def estimate_energy_value(
    energy_kwh: float,
    electricity_price_per_kwh: float,
) -> float:
    return round(max(energy_kwh, 0.0) * electricity_price_per_kwh, 2)


def build_financial_assumptions(
    electricity_price_per_kwh: float,
    currency: str,
    system_capex: float,
    valuation_basis: str = "Estimated gross value from forecasted energy at the configured tariff.",
) -> dict:
    return {
        "electricity_price_per_kwh": round(electricity_price_per_kwh, 4),
        "currency": currency,
        "system_capex": round(system_capex, 2),
        "valuation_basis": valuation_basis,
        "annual_savings_basis": (
            "Annual savings are assumed to equal the estimated yearly energy value at the "
            "configured tariff."
        ),
        "payback_basis": (
            "Simple payback = system CAPEX / annual savings. It ignores financing, taxes, "
            "degradation, maintenance, export limits, and time-varying tariffs."
        ),
    }


def build_financial_summary(
    monthly_kwh: Iterable[float],
    electricity_price_per_kwh: float,
    currency: str,
    system_capex: float,
) -> dict:
    monthly_kwh_list = [round(float(value), 1) for value in monthly_kwh]
    monthly_estimated_value = [
        estimate_energy_value(value, electricity_price_per_kwh)
        for value in monthly_kwh_list
    ]
    yearly_kwh = round(sum(monthly_kwh_list), 1)
    yearly_estimated_value = round(sum(monthly_estimated_value), 2)
    annual_savings = yearly_estimated_value

    return {
        "monthly_estimated_value": monthly_estimated_value,
        "yearly_estimated_value": yearly_estimated_value,
        "annual_savings": annual_savings,
        "simple_payback_years": calculate_simple_payback_years(
            system_capex=system_capex,
            annual_savings=annual_savings,
        ),
        "avg_monthly_estimated_value": round(yearly_estimated_value / 12, 2),
        "financial_assumptions": build_financial_assumptions(
            electricity_price_per_kwh=electricity_price_per_kwh,
            currency=currency,
            system_capex=system_capex,
            valuation_basis=(
                "Estimated self-consumption or feed-in value from forecasted yearly energy "
                "using the configured tariff."
            ),
        ),
        "yearly_kwh": yearly_kwh,
    }
