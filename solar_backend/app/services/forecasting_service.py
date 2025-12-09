import pandas as pd

def simple_yearly_forecast(daily_production: list):
    """
    Placeholder – later we replace with Prophet or LSTM.
    """
    year_sum = sum(daily_production) * 365 / len(daily_production)
    return {"estimated_annual_energy_kwh": round(year_sum, 2)}
