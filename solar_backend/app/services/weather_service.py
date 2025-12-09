import requests
from app.config import WEATHER_API_URL

def get_weather_forecast(lat: float, lon: float, days: int = 7):
    """
    Fetch solar irradiance forecast from external API.
    For prototype we use Open-Meteo's free forecast.
    """
    url = (
        f"{WEATHER_API_URL}?latitude={lat}&longitude={lon}"
        f"&hourly=shortwave_radiation&forecast_days={days}"
    )
    res = requests.get(url)
    res.raise_for_status()
    data = res.json()

    return data
