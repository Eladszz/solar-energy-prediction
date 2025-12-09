import requests
from app.config import WEATHER_API_URL

def get_weather_forecast(lat: float, lon: float, days: int = 1):
    url = (
        f"{WEATHER_API_URL}?latitude={lat}&longitude={lon}"
        "&hourly=shortwave_radiation,temperature_2m"
        f"&forecast_days={days}"
    )

