import requests
from app.config import WEATHER_API_URL
import logging

logger = logging.getLogger(__name__)


def get_weather_forecast(lat: float, lon: float, days: int = 1):
    """
    Retrieve hourly shortwave radiation and temperature forecast.
    """
    url = (
        WEATHER_API_URL + f"?latitude={lat}&longitude={lon}"
        "&hourly=shortwave_radiation,temperature_2m"
        f"&forecast_days={days}"
        "&past_days=0"
        "&timezone=auto"
    )

    logger.info(f"Fetching weather forecast for lat: {lat}, lon: {lon}, days: {days}")
    try:
        res = requests.get(url)
        res.raise_for_status()
        logger.info(
            f"Received weather forecast data with status code {res.status_code}"
        )
        data = res.json()
        logger.info(f"Forecast data keys: {list(data.keys())}")
        # Must have "hourly"
        if "hourly" not in data:
            print("⚠ No 'hourly' in forecast API response")
            return None
        return data
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return None
