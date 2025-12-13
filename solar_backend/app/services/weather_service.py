import requests
from app.config import WEATHER_API_URL

def get_weather_forecast(lat: float, lon: float, days: int = 1):
    """
    Retrieve hourly shortwave radiation and temperature forecast.
    """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=shortwave_radiation,temperature_2m"
        f"&forecast_days={days}"
        "&past_days=0"
    )

    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        # Must have "hourly"
        if "hourly" not in data:
            print("⚠ No 'hourly' in forecast API response")
            return None
        return data
    except Exception as e:
        print("⚠ Weather API error:", e)
        return None
