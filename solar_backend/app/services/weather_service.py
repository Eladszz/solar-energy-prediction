from app.config import WEATHER_API_URL
import logging
import requests

from app.services.external_service import (
    DEFAULT_EXTERNAL_TIMEOUT_SECONDS,
    fetch_json_from_provider,
    require_list_fields,
)

from app.exceptions.external_service_exceptions import ExternalServiceResponseError

logger = logging.getLogger(__name__)
WEATHER_FORECAST_PROVIDER = "Weather forecast provider"
WEATHER_FORECAST_TIMEOUT_SECONDS = DEFAULT_EXTERNAL_TIMEOUT_SECONDS


def get_weather_forecast(
    lat: float,
    lon: float,
    days: int = 1,
):
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
    data = fetch_json_from_provider(
        url=url,
        provider=WEATHER_FORECAST_PROVIDER,
        timeout=WEATHER_FORECAST_TIMEOUT_SECONDS,
        request_get=requests.get,
    )
    logger.info("Received weather forecast data with keys: %s", list(data.keys()))

    hourly = data.get("hourly")
    if not isinstance(hourly, dict):
        raise ExternalServiceResponseError(
            provider=WEATHER_FORECAST_PROVIDER,
            user_message="Weather forecast provider returned malformed hourly data. Please try again shortly.",
            detail="Missing 'hourly' object in forecast response.",
        )

    require_list_fields(
        container=hourly,
        fields=("time", "shortwave_radiation", "temperature_2m"),
        provider=WEATHER_FORECAST_PROVIDER,
        context="forecast hourly data",
    )
    return data
